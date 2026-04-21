# Skill Gap Analyzer 🚀

## 📌 Problem Statement
The curriculum followed by many colleges is often not aligned with current job market trends. As a result, students graduate without hands-on experience in industry-relevant tools and technologies. Many students are also unaware of which skills they need to learn and which skills are currently in high demand.

This mismatch between academic curriculum and industry requirements leads to a significant skill gap, reducing students’ employability.

The Skill Gap Analyzer aims to bridge this gap by analyzing resumes, extracting skills, and comparing them with industry demand to provide personalized skill recommendations.

---

## 🧠 Project Overview
Skill Gap Analyzer is an AI-powered platform that helps students identify missing skills based on their resumes and current job market trends. The system extracts skills from resumes, analyzes industry requirements using job data, and provides intelligent recommendations for career growth.

---

## 🏗️ System Architecture
The system consists of a modern full-stack architecture including:
- Frontend (Next.js + React)
- Backend (Django + DRF)
- AI/ML models for skill extraction and analysis
- External APIs for job market data
- PostgreSQL database for storage

The architecture diagram (in the document) shows interaction between frontend, backend services, AI modules, and database layers.

---

## 🔄 Sequence Diagram
The sequence flow includes:
1. User registration and login
2. Resume upload
3. Skill extraction using NLP and AI models
4. Job market data fetching via APIs
5. Skill gap analysis
6. Recommendations generation
7. Visualization of analytics and insights

(Refer to the sequence diagram in the provided documentation for detailed workflow.)

---

## 🛠️ Tech Stack

### 🎨 Frontend
- Next.js
- React
- Tailwind CSS
- Axios
- Recharts.js

### ⚙️ Backend
- Python
- Django
- Django REST Framework
- spaCy (NLP)
- Beautiful Soup (Web Scraping)
- Data Preprocessing
- FAISS (Vector Search)
- Sentence Transformers
- PyMuPDF (PDF Text Extraction)
- LLM (Google AI Studio API)
- APScheduler (Task Scheduling)
- Supabase
- Adzuna API (Job Market Data)

---

## 🔐 Security & Authentication
- JWT (JSON Web Token Authentication)
- HTTPS Secure Communication

---

## 🗄️ Database
- PostgreSQL

---

## 🤖 Key Features
- 📄 Resume Upload and Parsing
- 🧠 AI-Based Skill Extraction
- 📊 Skill Gap Analysis
- 📈 Job Market Trend Analysis
- 🎯 Personalized Skill Recommendations
- 📉 Data Visualization and Analytics Dashboard
- 🔍 Industry Skill Matching using AI Models

---

## 📊 How It Works
1. User registers and logs into the platform.
2. User uploads their resume (PDF).
3. The system extracts text using PyMuPDF.
4. NLP and AI models extract skills from the resume.
5. Job market data is collected using APIs.
6. The system compares user skills with industry-required skills.
7. Skill gap is identified and recommendations are generated.
8. Results are displayed through an interactive dashboard.

---

## Project Structure

project/
├── backend/
│   ├── apps/
│   │   ├── accounts/      # Custom User, JWT auth, HTTP-only cookies
│   │   ├── documents/     # Supabase pre-signed uploads, PyMuPDF parsing
│   │   ├── skills/        # Hybrid extraction, MASTER_SKILLS
│   │   ├── roles/         # Role, RoleSkill
│   │   ├── embeddings/    # Skill/RoleEmbedding, FAISS build
│   │   ├── recommendations/  # Top roles, skill gap, learning plan
│   │   ├── jobs/          # Adzuna ingestion, scheduler
│   │   ├── analytics/     # Dashboard API
│   │   └── chatbot/       # Google AI Studio
│   ├── core/
│   │   ├── middleware/    # Rate limit, CSRF cookie
│   │   ├── services/      # Supabase, document parser, skill extractor, embeddings, FAISS, ranking, skill gap, learning, Adzuna
│   ├── config/            # Settings, URLs
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/               # Next.js App Router
│   │   ├── dashboard/     # Overview, Documents, Skills, Roles, Jobs, Chat
│   │   ├── login/, register/
│   ├── src/lib/           # api.ts (Axios + credentials)
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md

---

## Quick Start

### Backend

```bash
cd backend
cp ../.env.example ../.env
# Edit .env with SECRET_KEY, DATABASE_URL, etc.

python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# PostgreSQL required
python manage.py migrate
python manage.py seed_roles
python manage.py build_faiss_index
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
# Set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local
npm run dev
```

---

## 🚀 Future Enhancements
- Real-time job market integration
- Advanced AI skill recommendation engine
- Multi-language resume support
- Career roadmap generation
- Mobile application support

---

## 👨‍💻 Use Case
This project is especially useful for:
- Students
- Fresh Graduates
- Career Switchers
- Educational Institutions
- Training Platforms

It helps users understand industry demands and improve their employability by learning the right skills.

---

## 📚 Conclusion
The Skill Gap Analyzer bridges the gap between academic learning and industry requirements by leveraging AI, NLP, and real-time job data. It empowers students with actionable insights and personalized recommendations to enhance their career readiness.