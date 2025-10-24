import sys
import os
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, create_engine
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Database setup (inline to avoid import issues)
def get_database_url():
    """Get database URL based on environment"""
    if os.getenv("INSTANCE_CONNECTION_NAME"):
        # Cloud Run with Cloud SQL Proxy
        return f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:5432/{os.getenv('DB_NAME', 'aurelia_concepts')}"
    else:
        # Direct connection
        return f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'AureliaTeam2025')}@{os.getenv('DB_HOST', '34.136.16.4')}:5432/{os.getenv('DB_NAME', 'aurelia_concepts')}"

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ConceptNote(Base):
    __tablename__ = "concept_notes"

    id = Column(Integer, primary_key=True, index=True)
    concept_name = Column(String(255), unique=True, index=True, nullable=False)
    definition = Column(Text, nullable=False)
    formula = Column(Text, nullable=True)
    example = Column(Text, nullable=False)
    applications = Column(JSON, nullable=False)
    source = Column(String(50), nullable=False)
    pdf_references = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ✅ NO key_points field

    def to_dict(self):
        """Convert model to dictionary for API responses"""
        return {
            "concept_name": self.concept_name,
            "definition": self.definition,
            "formula": self.formula if self.formula else "",
            "example": self.example,
            "applications": self.applications or [],
            "source": self.source,
            "pdf_references": self.pdf_references or []
        }

class ConceptNoteCRUD:
    """CRUD operations for ConceptNote"""
    
    @staticmethod
    def create_concept(db: Session, concept_data: dict) -> ConceptNote:
        """Create new concept note"""
        # ✅ Filter out invalid fields (like 'key_points' if passed)
        allowed_fields = {
            'concept_name', 'definition', 'formula', 'example', 
            'applications', 'source', 'pdf_references'
        }
        
        filtered_data = {
            key: value for key, value in concept_data.items() 
            if key in allowed_fields
        }
        
        # ✅ Ensure required fields have defaults
        if 'definition' not in filtered_data or not filtered_data['definition']:
            filtered_data['definition'] = f"{filtered_data.get('concept_name', 'Unknown')} - No definition available."
        
        if 'example' not in filtered_data or not filtered_data['example']:
            filtered_data['example'] = f"Example for {filtered_data.get('concept_name', 'concept')} not available."
        
        if 'applications' not in filtered_data or not filtered_data['applications']:
            filtered_data['applications'] = ["General financial analysis"]
        
        if 'source' not in filtered_data or not filtered_data['source']:
            filtered_data['source'] = 'unknown'
        
        try:
            concept = ConceptNote(**filtered_data)
            db.add(concept)
            db.commit()
            db.refresh(concept)
            logger.info(f"✅ Created concept: {filtered_data.get('concept_name')}")
            return concept
        except Exception as e:
            logger.error(f"❌ Error creating concept: {e}")
            db.rollback()
            raise
    
    @staticmethod
    def get_concept(db: Session, concept_name: str) -> Optional[ConceptNote]:
        """Get concept by name (case-insensitive)"""
        return db.query(ConceptNote).filter(
            ConceptNote.concept_name.ilike(concept_name)
        ).first()
    
    @staticmethod
    def get_all_concepts(db: Session, limit: int = 50) -> List[ConceptNote]:
        """Get all concepts with limit"""
        return db.query(ConceptNote).order_by(
            ConceptNote.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def update_concept(db: Session, concept: ConceptNote, concept_data: dict) -> ConceptNote:
        """Update existing concept"""
        allowed_fields = {
            'concept_name', 'definition', 'formula', 'example', 
            'applications', 'source', 'pdf_references'
        }
        
        for key, value in concept_data.items():
            if key in allowed_fields and hasattr(concept, key):
                setattr(concept, key, value)
        
        concept.updated_at = func.now()
        db.commit()
        db.refresh(concept)
        return concept
    
    @staticmethod
    def get_stats(db: Session) -> dict:
        """Get database statistics"""
        total_concepts = db.query(ConceptNote).count()
        fintbx_count = db.query(ConceptNote).filter(
            ConceptNote.source.in_(['fintbx', 'chromadb'])
        ).count()
        wiki_count = db.query(ConceptNote).filter(
            ConceptNote.source == 'wikipedia'
        ).count()
        
        return {
            "total_concepts": total_concepts,
            "fintbx_concepts": fintbx_count,
            "wikipedia_concepts": wiki_count
        }

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
        
        # Add sample data
        db = SessionLocal()
        try:
            existing = db.query(ConceptNote).first()
            if not existing:
                sample_concept = ConceptNote(
                    concept_name="Duration",
                    definition="Duration measures the price sensitivity of a bond to changes in interest rates.",
                    formula="Modified Duration = Macaulay Duration / (1 + YTM/n)",
                    example="A bond with duration of 5 years will decrease in price by approximately 5% for each 1% increase in interest rates.",
                    applications=["Interest rate risk management", "Portfolio immunization", "Bond portfolio management"],
                    source="fintbx",
                    pdf_references=[15, 16]
                )
                db.add(sample_concept)
                db.commit()
                print("✅ Sample data added!")
        except Exception as e:
            print(f"⚠️  Sample data error (may already exist): {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise

if __name__ == "__main__":
    init_db()