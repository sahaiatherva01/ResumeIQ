# ResumeLens AI — ATS+ Resume Intelligence Engine

ResumeLens AI is an intelligent, single-page web application that analyzes PDF or DOCX resumes in isolation. It parses document structure, runs layout compatibility audits, uses Gemini AI for structured extraction, and scores the resume against a programmatic, transparent rubric.

## Key Features

1. **Structured Candidate Profile**: Deep LLM extraction of contact info, education history, detailed work experience, personal projects, certifications, and achievements.
2. **ATS+ Score**: An overall 0–100 score based on a transparent, 105-point analytical rubric.
3. **ATS Compatibility checks**: Programmatic detection of formatting risks (two-column sidebar layouts), scanned/image-only text, missing standard sections, incomplete contact info, inconsistent dates, long paragraphs, and passive bullets.
4. **Skill Intelligence**: Extractions, categorization (languages, frameworks, cloud, databases), and dynamic normalization (e.g. mapping "ML" to "Machine Learning").
5. **Achievement & Impact Analysis**: Scans bullet points using custom regex patterns for percentages, counts, metrics, and dollar values. Shows suggestions on exactly how to quantify passive bullets.
6. **Recruiter Summaries**: AI-synthesized summaries, key strengths, and areas of improvement.

---

## Tech Stack
* **Frontend**: HTML5, CSS3 (Glassmorphic Dark Theme), and Vanilla JavaScript (No React/Vue frameworks).
* **Backend**: Python + Flask REST API.
* **Document Parsing**: PyMuPDF (fitz) for PDF text extraction & layout coordinates, python-docx for DOCX files.
* **LLM Engine**: Gemini API (`gemini-1.5-flash`) via the `google-generativeai` SDK, with Pydantic schemas validating output.

---

## ATS+ Scoring Rubric

All scoring in the app is labeled under the **ATS+ scoring framework**. It represents a transparent analytical rubric and is not a replication of any proprietary corporate ATS algorithm.

| Category | Max points | Description |
|---|---|---|
| ATS Compatibility | 20 | Passes parsing audits (no sidebars, clean text, contact info) |
| Resume Structure | 20 | Formatting risks, missing sections, and layout cleanliness |
| Content Quality | 20 | Use of strong technical action verbs in experience bullets |
| Skills Representation | 20 | Skills volume, categorization, and normalization completeness |
| Keyword Quality | 10 | Coverage of key terms mapping to tech domain fields |
| Completeness | 10 | Section coverage percent (Contact info, Education, Experience, etc.) |
| Quantified Achievements | 5 | Count of quantified, metric-backed impact statements |
| **Total (raw)** | **105** | Normalized to **0–100** for dashboard presentation |

---

## Getting Started

### 1. Installation

Clone this repository and navigate to the project directory:
```bash
cd ResumeLens_AI
```

Create a virtual environment and install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root folder (or copy `.env.example`):
```bash
cp .env.example .env
```

Open `.env` and fill in your Gemini API key:
```env
GEMINI_API_KEY=AIzaSy...your_gemini_api_key...
PORT=5000
```
> **Note**: If `GEMINI_API_KEY` is not provided or set to a placeholder, the backend will run in a **demo mock mode** using prepopulated candidate data. This allows testing all frontend UI animations and layouts without calling the Gemini API.

### 3. Running Locally

Run the Flask application:
```bash
python app.py
```

The application will launch on: [http://localhost:5000](http://localhost:5000)

---

## API Endpoints

* **`GET /`**: Renders the frontend single-page dashboard.
* **`GET /api/health`**: Returns a simple health check status.
* **`POST /api/upload`**: Validates a document (PDF/DOCX), parses its raw text, and returns basic layout metadata.
* **`POST /api/analyze`**: Standard analysis pipeline. Accepts a PDF/DOCX multipart upload or a JSON text payload. Returns the fully populated structured `CandidateProfile` JSON.
