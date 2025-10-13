# AURELIA - Automated Financial Concept Note Generator

> AI-powered RAG system for generating standardized financial concept notes

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-Educational-yellow.svg)]()

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Team](#team)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

AURELIA is a production-grade microservice that automatically generates comprehensive concept notes for financial topics. The system uses Retrieval-Augmented Generation (RAG) to extract content from the Financial Toolbox User's Guide (fintbx.pdf) and falls back to Wikipedia when concepts aren't found in the primary source.

**Course:** DAMG6210 - Database Management Systems  
**Institution:** Northeastern University  
**Project Type:** Case Study 3 - RAG System Implementation

---

## ✨ Features

### Core Capabilities
- 🔍 **Intelligent Retrieval**: PDF-first search with Wikipedia fallback
- 📊 **Structured Output**: Consistent JSON schema using Instructor
- 💾 **Smart Caching**: PostgreSQL-backed cache for instant retrieval
- ⚡ **Dual Vector Stores**: Support for both Pinecone and ChromaDB
- 🔄 **Automated Pipelines**: Airflow DAGs for batch processing
- ☁️ **Cloud-Native**: Fully deployed on GCP

### Generation Features
- Definition with clear explanations
- Mathematical formulas (when applicable)
- Practical examples
- Real-world applications
- Source citations with page references

---

## 🏗️ Architecture