import sys
import os
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, create_engine
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional

# Database setup (inline to avoid import issues)
DATABASE_URL = "postgresql://postgres:AureliaTeam2025@127.0.0.1:5432/aurelia_concepts"
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database session dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

    def to_dict(self):
        return {
            "id": self.id,
            "concept_name": self.concept_name,
            "definition": self.definition,
            "formula": self.formula,
            "example": self.example,
            "applications": self.applications or [],
            "source": self.source,
            "pdf_references": self.pdf_references or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ConceptNoteCRUD:
    @staticmethod
    def create_concept(db: Session, concept_data: dict) -> ConceptNote:
        concept = ConceptNote(**concept_data)
        db.add(concept)
        db.commit()
        db.refresh(concept)
        return concept
    
    @staticmethod
    def get_concept(db: Session, concept_name: str) -> Optional[ConceptNote]:
        return db.query(ConceptNote).filter(
            ConceptNote.concept_name.ilike(concept_name)
        ).first()
    
    @staticmethod
    def get_all_concepts(db: Session, limit: int = 50) -> List[ConceptNote]:
        return db.query(ConceptNote).order_by(
            ConceptNote.updated_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_stats(db: Session) -> dict:
        total_concepts = db.query(ConceptNote).count()
        fintbx_count = db.query(ConceptNote).filter(ConceptNote.source == 'fintbx').count()
        wiki_count = db.query(ConceptNote).filter(ConceptNote.source == 'wikipedia').count()
        
        return {
            "total_concepts": total_concepts,
            "fintbx_concepts": fintbx_count,
            "wikipedia_concepts": wiki_count
        }

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
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
                applications=["Interest rate risk management", "Portfolio immunization"],
                source="system",
                pdf_references=[]
            )
            db.add(sample_concept)
            db.commit()
            print("Sample data added!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()