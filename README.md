# ResumeIQ

### AI-Powered Resume Intelligence & ATS Analyzer

ResumeIQ is an AI-powered resume analysis platform that helps candidates understand how their resume performs from an ATS-oriented and recruiter perspective.

It extracts the actual information present in a resume, structures it into a candidate profile, evaluates resume quality and ATS compatibility, calculates an overall analytical ATS score, identifies strengths and weaknesses, and provides actionable improvement insights.

> **Don't just tell candidates that their resume needs improvement. Show them why.**

---


##  Features

###  Real Resume Data Extraction

ResumeIQ extracts information directly from the uploaded resume instead of relying on predefined or assumed candidate information.

It identifies:

- Personal Information
- Education
- Work Experience
- Projects
- Skills
- Certifications
- Achievements
- Resume Bullet Points

The extracted information is displayed in a structured candidate profile so users can verify what the system understood from their resume.

###  Overall ATS Score

ResumeIQ generates a single overall ATS-oriented score based on multiple measurable resume signals.

The score is presented as **one combined score**, while the dashboard also shows how the score is distributed across different analysis categories.

The analysis considers:

- ATS Compatibility
- Resume Structure
- Keyword / Job Relevance
- Content Quality
- Skills Representation
- Quantified Impact
- Resume Completeness
- Readability & Consistency

The goal is to provide a practical estimate of resume readiness rather than claiming to reproduce the proprietary scoring system of any specific ATS.

###  AI Recruiter Intelligence

ResumeIQ provides recruiter-style insights based on the actual resume content.

It identifies:

- Candidate strengths
- Key weaknesses
- Important areas requiring attention
- Resume quality observations
- Actionable improvement recommendations

###  ATS Compatibility Analysis

The platform performs multiple ATS-oriented checks to identify potential parsing and resume-quality issues.

Examples include:

- Contact Information
- Critical Resume Sections
- Resume Column Layout
- Text Extraction Quality
- Employment Dates
- Text Paragraph Lengths
- Measurable Outcomes
- Bullet Point Formatting

Each check is presented with a clear status:

**Pass / Warning / Fail**

###  Skill Analysis

ResumeIQ extracts technical skills from the actual resume and organizes them into categories.

Examples include:

- Programming Languages
- Frameworks & Libraries
- AI/ML Technologies
- GenAI & LLMs
- Tools
- Core Competencies

The system also analyzes the relative strength of different technical domains represented in the resume.

###  Quantified Impact Analysis

ResumeIQ analyzes experience and project bullet points to determine whether they communicate measurable impact.

It detects bullets that lack measurable outcomes and highlights opportunities to improve them using genuine metrics such as:

- Accuracy
- Performance
- Speed
- Latency
- Scale
- Efficiency
- Time saved
- Cost reduction

The system does **not invent achievements or metrics**.

Instead, it identifies where the candidate could add real measurable results.

###  Resume Completeness

ResumeIQ checks whether important resume sections are present.

It can identify sections such as:

- Contact Information
- Education
- Work Experience
- Skills
- Projects
- Certifications
- Achievements

###  Extracted Resume Profile

Users can inspect the structured profile generated from their resume.

The profile includes:

- Personal Information
- Education
- Experience
- Projects
- Skills
- Certifications
- Achievements

###  Detailed Category Analysis

The dashboard provides deeper analysis of individual resume-quality categories.

Users can understand not only their final score, but also **why** the score was generated and which areas are affecting it.

###  Resume Analysis Report

The report contains:

- Overall ATS Score
- Score Distribution
- Strengths
- Key Issues
- Priority Areas
- ATS Compatibility Checks
- Skill Analysis
- Quantified Impact Analysis
- Resume Completeness
- Extracted Resume Profile

---

#  How ResumeIQ Works

```text
                    ┌──────────────────────┐
                    │     Resume Upload    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   PDF Text Extraction│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Resume Information  │
                    │      Extraction      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Structured Candidate │
                    │       Profile        │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
      │ ATS Checks  │   │ Skill & NLP │   │  Content    │
      │             │   │  Analysis   │   │  Analysis   │
      └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │    ATS Score Engine  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ AI Recruiter Insights│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Interactive Report │
                    └──────────────────────┘
```

---

#  Tech Stack

## Frontend

- HTML5
- CSS3
- JavaScript

## Backend

- Python
- Flask
- REST APIs

## AI / NLP

- Generative AI
- Google Gemini API
- Natural Language Processing
- Structured information extraction
- Resume content analysis

## Document Processing

- PDF text extraction
- Resume parsing
- Candidate profile generation

## Deployment

- Render

---

# 📂 Project Structure

```text
ResumeIQ/
│
├── static/
│   ├── style.css
│   └── script.js
│
├── templates/
│   └── index.html
│
├── data/
│
├── app.py
├── ats_analyzer.py
├── extractor.py
├── resume_parser.py
├── schemas.py
├── prompts.py
├── verify_scoring.py
├── create_test_resume.py
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

#  Installation

## 1. Clone the repository

```bash
git clone https://github.com/sahaiatherva01/ResumeIQ.git
cd ResumeIQ
```

## 2. Create a virtual environment

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

You can use `.env.example` as a reference.

**Never commit your real API key to GitHub.**

## 5. Run the application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

---

#  Environment Variables

ResumeIQ uses environment variables for sensitive configuration.

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

The actual `.env` file should remain local and must not be committed to the repository.

---

#  Analysis Pipeline

1. **Upload** — The user uploads their resume.
2. **Extract** — The application extracts readable text from the document.
3. **Parse** — Extracted text is converted into structured candidate information.
4. **Validate** — Important resume information and sections are checked.
5. **Analyze** — Resume structure, ATS compatibility, skills, content quality, keywords, readability, quantified impact, and completeness are evaluated.
6. **Score** — Analysis signals are combined into a single overall ATS-oriented score.
7. **Generate Insights** — Strengths, weaknesses, and improvement opportunities are identified.
8. **Present** — Results are displayed through an interactive dashboard.

---

#  Why ResumeIQ?

A resume is often the first filter between a candidate and an opportunity.

Candidates usually don't know:

- Whether their resume is machine-readable
- Whether important information is being extracted correctly
- Whether their skills are represented clearly
- Whether their experience demonstrates measurable impact
- Whether their resume structure is ATS-friendly
- Which weaknesses could affect recruiter perception

ResumeIQ was built to make this process more transparent.

Instead of simply saying:

> **"Your resume needs improvement."**

ResumeIQ tries to answer:

> **"What is working, what is not, and why?"**

---

# ⚠️ Disclaimer

ResumeIQ provides an analytical estimate based on its own ATS-oriented resume analysis framework.

It does **not** reproduce the proprietary scoring system of any specific Applicant Tracking System.

Different ATS platforms may parse, rank, and evaluate resumes differently.

Therefore, the ResumeIQ score should be treated as an **analytical resume-readiness indicator**, not an official ATS score.

---
