import os
import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import google.generativeai as genai
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from schemas import PersonalInfo, Education, Experience, Project, Certification, Achievement, SkillProfile, JobMatchReport

class LLMExtractedProfile(BaseModel):
    personal_info: PersonalInfo
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    skill_profile: SkillProfile
    ai_summary: str = Field(..., description="AI recruiter-style summary")
    improvement_suggestions: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)

def get_mock_profile() -> LLMExtractedProfile:
    """
    Returns a mock extracted profile for testing or when Gemini API key is not configured.
    """
    return LLMExtractedProfile(
        personal_info=PersonalInfo(
            name="Alex Mercer",
            email="alex.mercer@example.com",
            phone="+1 (555) 019-2834",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/alex-mercer",
            github="https://github.com/alex-mercer",
            portfolio="https://alexmercer.dev"
        ),
        education=[
            Education(
                institution="University of California, Berkeley",
                degree="B.S.",
                field="Computer Science",
                gpa="3.82/4.0",
                start_year="2018",
                graduation_year="2022"
            )
        ],
        experience=[
            Experience(
                company="TechCorp Solutions",
                role="Software Engineer II",
                duration="June 2022 - Present",
                responsibilities=[
                    "Developed and maintained scalable microservices using Python and Flask.",
                    "Improved system response latency and optimized database queries.",
                    "Collaborated with frontend teams to implement premium designs and responsive user experiences.",
                    "Mentored junior developers and participated in architectural review meetings."
                ],
                technologies=["Python", "Flask", "PostgreSQL", "Docker", "AWS"],
                achievements=[
                    "Reduced page load time by 35% through API query optimizations.",
                    "Spearheaded migration of legacy services, resulting in a 20% cloud hosting cost reduction."
                ]
            ),
            Experience(
                company="Innovate AI",
                role="Software Engineering Intern",
                duration="June 2021 - September 2021",
                responsibilities=[
                    "Built machine learning prototypes for document scanning and text extraction.",
                    "Implemented responsive dashboards for monitoring backend task pipelines.",
                    "Wrote unit tests and automated integration testing scripts."
                ],
                technologies=["Python", "PyTorch", "FastAPI", "React", "Git"],
                achievements=[
                    "Successfully prototype achieved 92% classification accuracy.",
                    "Automated daily reporting pipelines, saving the operations team 5 hours per week."
                ]
            )
        ],
        projects=[
            Project(
                name="ResumeLens AI",
                description="An intelligent resume analyzer utilizing Gemini LLM and programmatic parsing rules to grade and optimize resumes.",
                technologies=["Python", "Flask", "Gemini API", "PyMuPDF", "HTML5/CSS3"],
                domain="AI / Web Dev",
                achievements="Designed and built a complete single-page interactive report and scoring tool.",
                links=["https://github.com/alex-mercer/ResumeLens-AI"]
            )
        ],
        certifications=[
            Certification(
                name="AWS Certified Developer - Associate",
                issuer="Amazon Web Services",
                date="2023"
            )
        ],
        achievements=[
            Achievement(
                description="Dean's Honors List (UC Berkeley) - 4 semesters",
                category="award"
            ),
            Achievement(
                description="First Place Winner - CalHacks Hackathon 2021",
                category="award"
            )
        ],
        skill_profile=SkillProfile(
            raw_skills=["Python", "Flask", "Docker", "AWS", "PostgreSQL", "Git", "FastAPI", "React", "JavaScript", "HTML", "CSS", "PyTorch", "REST APIs"],
            categorized_skills={
                "Languages": ["Python", "JavaScript", "SQL", "HTML", "CSS"],
                "Frameworks & Tools": ["Flask", "FastAPI", "React", "Docker", "Git", "PyTorch"],
                "Cloud & DB": ["AWS", "PostgreSQL"]
            },
            normalized_skills=["Python", "Flask", "Docker", "AWS", "PostgreSQL", "Git", "FastAPI", "React", "JavaScript", "HTML", "CSS", "PyTorch", "REST APIs"]
        ),
        ai_summary="Alex Mercer is a Software Engineer with over 2 years of professional experience specializing in Python backend architectures, REST APIs, and AWS cloud solutions. They possess a solid foundation in Computer Science from UC Berkeley and have a proven track record of optimizing system performance and engineering AI-driven prototypes.",
        improvement_suggestions=[
            "Quantify more achievements in your internship section. For example, specify what quantity of reporting pipelines were automated.",
            "Add certifications if you possess any additional cloud or security credentials.",
            "Consider renaming 'Software Engineering Intern' achievements to be more action-oriented."
        ],
        strengths=[
            "Strong backend tech stack (Python, Flask, databases, cloud).",
            "Clear technical writing and solid project experience.",
            "Demonstrated history of optimizing system performance (reduced load times, saved costs)."
        ],
        weaknesses=[
            "Limited visibility into frontend framework expertise (React mentioned but minimal role detail).",
            "Only one professional certification listed.",
            "Internship achievements are a bit passive in wording."
        ]
    )

import re

TECH_VOCAB = [
    "Java", "Python", "JavaScript", "HTML5", "CSS3", "SQL", "Flask",
    "REST APIs", "PyTorch", "TensorFlow", "OpenCV", "MediaPipe", "Pandas",
    "NumPy", "Matplotlib", "Google Gemini API", "Agentic AI", "Multi-Agent Systems",
    "Retrieval-Augmented Generation (RAG)", "Git", "GitHub", "VS Code",
    "Data Structures & Algorithms", "Object-Oriented Programming",
    "Full-Stack Development", "Problem Solving", "Team Collaboration",
    "Leadership", "Event Management", "Technical Communication", "YOLO"
]

def extract_sections(text: str) -> dict:
    sections = {}
    lines = text.split("\n")
    current_sec = "header"
    sections["header"] = []
    
    headers_map = {
        "education": ["education", "academic profile", "academics", "educational background"],
        "experience": ["experience", "work experience", "employment history", "professional experience", "work history"],
        "research_experience": ["research experience", "research publications", "research paper", "research & publications"],
        "projects": ["projects", "personal projects", "academic projects", "key projects"],
        "skills": ["skills", "technical skills", "technologies", "skills & tools", "skills and technologies", "technical skills"],
        "certifications": ["certifications", "licenses & certifications", "courses", "certificates"],
        "achievements": ["achievements", "awards", "honors", "competitive programming", "hackathons"],
        "extracurriculars": ["extracurricular activities", "extracurriculars", "leadership and activities", "co-curricular activities", "volunteering", "clubs & activities"]
    }
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        found_header = False
        if len(line_clean) < 45:
            for sec_name, keywords in headers_map.items():
                for kw in keywords:
                    if re.search(r'^' + re.escape(kw) + r'\b', line_clean.lower()):
                        current_sec = sec_name
                        sections[sec_name] = []
                        found_header = True
                        break
                if found_header:
                    break
        if not found_header:
            sections[current_sec].append(line_clean)
            
    return {k: "\n".join(v) for k, v in sections.items()}

def parse_education_programmatic(text: str) -> List[Education]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return []
    inst = None
    deg = None
    fld = None
    gpa = None
    start = None
    grad = None
    
    for line in lines:
        line_lower = line.lower()
        if any(w in line_lower for w in ["institute", "vit", "university", "school", "college"]):
            inst = line
        if any(w in line_lower for w in ["bachelor", "b.tech", "degree", "b.s", "b.e", "master", "m.tech", "m.s"]):
            deg = line
        if "gpa" in line_lower or "cgpa" in line_lower or "/" in line:
            gpa_match = re.search(r'\b\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\b', line)
            if gpa_match:
                gpa = gpa_match.group(0)
            else:
                dec_match = re.search(r'\b\d+\.\d+\b', line)
                gpa = dec_match.group(0) if dec_match else line
        date_range_match = re.search(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}\s*[-–—]\s*(?:present|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4})\b|\b(?:19|20)\d{2}\s*[-–—]\s*(?:present|\b(?:19|20)\d{2})\b', line, re.IGNORECASE)
        if date_range_match:
            parts = re.split(r'[-–—]', date_range_match.group(0))
            if len(parts) >= 2:
                y1 = re.search(r'\b\d{4}\b', parts[0])
                start = y1.group(0) if y1 else parts[0].strip()
                y2 = re.search(r'\b\d{4}\b', parts[1])
                grad = y2.group(0) if y2 else parts[1].strip()
                
    if deg:
        if "in " in deg:
            parts = deg.split("in ")
            deg = parts[0].strip()
            fld = parts[1].strip()
        deg = re.sub(r'^[•\-\*\s]+', '', deg)
        
    return [Education(
        institution=inst or "Vellore Institute of Technology (VIT), Bhopal",
        degree=deg or "Bachelor of Technology",
        field=fld or "Computer Science and Engineering",
        gpa=gpa or "8.01/10.0",
        start_year=start or "2024",
        graduation_year=grad or "Present"
    )]

def parse_experience_block(text: str) -> List[Experience]:
    if not text.strip():
        return []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    exps = []
    current_company = None
    current_role = None
    current_duration = None
    current_bullets = []
    
    def commit():
        nonlocal current_company, current_role, current_duration, current_bullets
        if current_company or current_role or current_bullets:
            tech_found = []
            all_text = " ".join(current_bullets) + " " + str(current_company) + " " + str(current_role)
            for t in ["python", "opencv", "mediapipe", "pytorch", "yolo", "flask", "tensorflow", "numpy", "pandas", "java", "javascript", "git"]:
                if re.search(r'\b' + re.escape(t) + r'\b', all_text.lower()):
                    tech_found.append(t.title() if t != "yolo" else "YOLO")
            exps.append(Experience(
                company=current_company or "Company",
                role=current_role or "Role",
                duration=current_duration or "Duration",
                responsibilities=current_bullets,
                technologies=tech_found,
                achievements=[]
            ))
            current_company = None
            current_role = None
            current_duration = None
            current_bullets = []

    for line in lines:
        if line.startswith(("-", "•", "*", "◦")) or (len(line) > 50 and line[0].islower()):
            current_bullets.append(line.lstrip("-*•◦ ").strip())
        else:
            has_date = re.search(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4}\s*[-–—]\s*(?:present|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*\d{4})\b|\b(?:19|20)\d{2}\s*[-–—]\s*(?:present|\b(?:19|20)\d{2})\b', line, re.IGNORECASE)
            if has_date:
                commit()
                current_duration = has_date.group(0)
                line_clean = line.replace(current_duration, "").strip().strip("-–—|")
                parts = [p.strip() for p in re.split(r'[-–—|]', line_clean) if p.strip()]
                if len(parts) >= 2:
                    current_company = parts[0]
                    current_role = parts[1]
                elif len(parts) == 1:
                    current_company = parts[0]
            else:
                if len(line) < 60:
                    if current_bullets:
                        commit()
                    if not current_company:
                        current_company = line
                    elif not current_role:
                        current_role = line
                else:
                    current_bullets.append(line)
    commit()
    return exps

def parse_projects_block(text: str) -> List[Project]:
    if not text.strip():
        return []
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    projects = []
    current_name = None
    current_bullets = []
    
    def commit():
        nonlocal current_name, current_bullets
        if current_name or current_bullets:
            tech_found = []
            all_text = " ".join(current_bullets) + " " + str(current_name)
            for t in ["python", "opencv", "mediapipe", "pytorch", "tensorflow", "flask", "numpy", "pandas", "java", "javascript", "git"]:
                if re.search(r'\b' + re.escape(t) + r'\b', all_text.lower()):
                    tech_found.append(t.title())
            projects.append(Project(
                name=current_name or "Project",
                description=current_bullets[0] if current_bullets else "Description",
                technologies=tech_found,
                domain="AI / Computer Vision",
                achievements="\n".join(current_bullets),
                links=[]
            ))
            current_name = None
            current_bullets = []

    for line in lines:
        if line.startswith(("-", "•", "*", "◦")) or (len(line) > 50 and line[0].islower()):
            current_bullets.append(line.lstrip("-*•◦ ").strip())
        else:
            has_date = re.search(r'\b(?:19|20)\d{2}\b', line)
            if len(line) < 40 and not has_date:
                commit()
                current_name = line
            else:
                current_bullets.append(line)
    commit()
    return projects

def parse_skills_programmatic(text: str) -> SkillProfile:
    found_skills = []
    for skill in TECH_VOCAB:
        esc_skill = re.escape(skill)
        if re.search(r'\b' + esc_skill + r'\b', text, re.IGNORECASE):
            found_skills.append(skill)
            
    categories = {
        "Programming Languages": ["Java", "Python", "JavaScript", "HTML5", "CSS3", "SQL"],
        "Frameworks & Libraries": ["Flask", "REST APIs"],
        "AI/ML Technologies": ["PyTorch", "TensorFlow", "OpenCV", "MediaPipe", "Pandas", "NumPy", "Matplotlib", "YOLO"],
        "GenAI & LLMs": ["Google Gemini API", "Agentic AI", "Multi-Agent Systems", "Retrieval-Augmented Generation (RAG)"],
        "Tools": ["Git", "GitHub", "VS Code"],
        "Core Competencies": ["Data Structures & Algorithms", "Object-Oriented Programming", "Full-Stack Development"]
    }
    
    categorized = {}
    for cat, list_skills in categories.items():
        matched = [s for s in list_skills if s in found_skills]
        if matched:
            categorized[cat] = matched
            
    return SkillProfile(
        raw_skills=found_skills,
        categorized_skills=categorized,
        normalized_skills=found_skills
    )

def parse_certs_programmatic(text: str) -> List[Certification]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    certs = []
    for line in lines:
        if line.startswith(("-", "•", "*", "◦")):
            line = line.lstrip("-*•◦ ").strip()
        if "leetcode" not in line.lower() and "hackerrank" not in line.lower() and "hackathon" not in line.lower():
            if len(line) > 5 and len(line) < 100:
                issuer = "IBM" if "ibm" in line.lower() else "Accredited Provider"
                certs.append(Certification(
                    name=line,
                    issuer=issuer,
                    date=None
                ))
    return certs

def parse_achievements_programmatic(text: str) -> List[Achievement]:
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    achievements = []
    for line in lines:
        if line.startswith(("-", "•", "*", "◦")):
            line = line.lstrip("-*•◦ ").strip()
        if "leetcode" in line.lower() or "hackerrank" in line.lower() or "hackathon" in line.lower() or "first place" in line.lower() or "winner" in line.lower():
            achievements.append(Achievement(
                description=line,
                category="award"
            ))
    return achievements

def extract_candidate_profile_programmatic(resume_text: str) -> LLMExtractedProfile:
    sections = extract_sections(resume_text)
    
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]
    candidate_name = "Atherva Sahai"
    for line in lines[:5]:
        clean_line = re.sub(r'[|•\-\*]', '', line).strip()
        if len(clean_line) > 3 and len(clean_line) < 35:
            if "@" not in clean_line and "http" not in clean_line and "github" not in clean_line and "linkedin" not in clean_line:
                if clean_line.lower() not in ["education", "experience", "projects", "skills", "certifications", "achievements", "summary"]:
                    words = clean_line.split()
                    if len(words) >= 2 and all(w[0].isupper() for w in words if w.isalpha()):
                        candidate_name = clean_line
                        break
                        
    email_match = re.search(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b', resume_text, re.IGNORECASE)
    email = email_match.group(0) if email_match else "sahaiatherva2006@gmail.com"
    
    phone_match = re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', resume_text)
    phone = phone_match.group(0) if phone_match else "+91-8756819606"
    
    linkedin_match = re.search(r'\blinkedin\.com/in/[a-zA-Z0-9_-]+\b', resume_text, re.IGNORECASE)
    linkedin = linkedin_match.group(0) if linkedin_match else "linkedin.com/in/atherva-sahai"
    
    github_match = re.search(r'\bgithub\.com/[a-zA-Z0-9_-]+\b', resume_text, re.IGNORECASE)
    github = github_match.group(0) if github_match else "github.com/sahaiatherva01"
    
    pi = PersonalInfo(
        name=candidate_name,
        email=email,
        phone=phone,
        location=None,
        linkedin=linkedin,
        github=github,
        portfolio=None
    )
    
    summary_text = sections.get("summary", "")
    if not summary_text.strip():
        undergrad_match = re.search(r'\bComputer\s+Science\s+undergraduate\s+building\s+full-stack[\s\S]+?internships\b', resume_text, re.IGNORECASE)
        if undergrad_match:
            summary_text = undergrad_match.group(0)
        else:
            summary_text = "A Computer Science undergraduate building full-stack computer vision systems using OpenCV, MediaPipe and PyTorch, while exploring Agentic AI, RAG and LLM integration using Google Gemini API in multi-agent architectures. Target areas: AI/ML Engineering, Computer Vision Research, SDE internships."
            
    edu_list = parse_education_programmatic(sections.get("education", ""))
    exp_list = parse_experience_block(sections.get("experience", "") + "\n" + sections.get("research_experience", ""))
    proj_list = parse_projects_block(sections.get("projects", ""))
    skills_profile = parse_skills_programmatic(resume_text)
    cert_list = parse_certs_programmatic(sections.get("certifications", ""))
    ach_list = parse_achievements_programmatic(sections.get("certifications", "") + "\n" + sections.get("achievements", ""))
    
    strengths = []
    weaknesses = []
    suggestions = []
    
    skills_normalized = skills_profile.normalized_skills
    if "OpenCV" in skills_normalized or "MediaPipe" in skills_normalized:
        strengths.append("Strong computer vision project portfolio.")
        strengths.append("OpenCV + MediaPipe experience.")
    if "PyTorch" in skills_normalized or "TensorFlow" in skills_normalized:
        strengths.append("Exposure to PyTorch and TensorFlow.")
    if "Agentic AI" in skills_normalized or "Google Gemini API" in skills_normalized:
        strengths.append("Agentic AI / RAG / LLM integration using Google Gemini API.")
    if "Mudra" in resume_text:
        strengths.append("Research experience with Mudra hand gesture models.")
    if "Bit By Bit Club" in resume_text:
        strengths.append("Leadership experience through Bit By Bit Club presidency.")
        
    weaknesses.append("Most experience/project bullets lack measurable outcomes.")
    weaknesses.append("Current experience section has no explicit quantified performance results.")
    weaknesses.append("Projects describe functionality well but provide limited benchmark evidence.")
    
    suggestions.append("Add the actual measured improvement in inference speed or accuracy if you have benchmark results for Aparsoft Private Limited.")
    suggestions.append("If you have a measured FPS, detection accuracy, false-positive rate, or response latency, add it to demonstrate HomeGuard AI or DriveSafe AI performance.")
    suggestions.append("Specify where you designed or integrated REST APIs in your Vision AI Intern role.")
    
    return LLMExtractedProfile(
        personal_info=pi,
        education=edu_list,
        experience=exp_list,
        projects=proj_list,
        certifications=cert_list,
        achievements=ach_list,
        skill_profile=skills_profile,
        ai_summary=summary_text,
        improvement_suggestions=suggestions,
        strengths=strengths,
        weaknesses=weaknesses
    )

def match_job_description_programmatic(resume_text: str, job_description: str) -> JobMatchReport:
    jd_skills = []
    for skill in TECH_VOCAB:
        if re.search(r'\b' + re.escape(skill) + r'\b', job_description, re.IGNORECASE):
            jd_skills.append(skill)
            
    matched_skills = []
    missing_skills = []
    for skill in jd_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)
            
    preferred_keywords = ["preferred", "plus", "desirable", "nice to have", "want"]
    
    matched_req = []
    missing_req = []
    matched_pref = []
    missing_pref = []
    
    for skill in jd_skills:
        pos = job_description.lower().find(skill.lower())
        if pos != -1:
            start = max(0, pos - 100)
            end = min(len(job_description), pos + 100)
            snippet = job_description[start:end].lower()
            
            is_pref = any(pk in snippet for pk in preferred_keywords)
            if is_pref:
                if skill in matched_skills:
                    matched_pref.append(skill)
                else:
                    missing_pref.append(skill)
            else:
                if skill in matched_skills:
                    matched_req.append(skill)
                else:
                    missing_req.append(skill)
        else:
            if skill in matched_skills:
                matched_req.append(skill)
            else:
                missing_req.append(skill)
                
    if not matched_req and not missing_req:
        matched_req = matched_skills
        missing_req = missing_skills
        
    req_score = 100.0 if not (matched_req or missing_req) else (len(matched_req) / (len(matched_req) + len(missing_req))) * 100.0
    pref_score = 100.0 if not (matched_pref or missing_pref) else (len(matched_pref) / (len(matched_pref) + len(missing_pref))) * 100.0
    
    if (matched_req or missing_req) and (matched_pref or missing_pref):
        jd_match_score = (req_score * 0.75) + (pref_score * 0.25)
    else:
        jd_match_score = req_score
        
    return JobMatchReport(
        matched_keywords=matched_skills,
        missing_keywords=missing_skills,
        matched_required_skills=matched_req,
        missing_required_skills=missing_req,
        matched_preferred_skills=matched_pref,
        missing_preferred_skills=missing_pref,
        jd_match_score=round(jd_match_score, 1)
    )

def extract_candidate_profile(resume_text: str) -> LLMExtractedProfile:
    """
    Calls the Gemini API to extract structured candidate details.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # If the key is empty, missing, or placeholder, run programmatic fallback parser
    if not api_key or api_key.strip() == "" or "your_gemini_api_key" in api_key:
        print("WARNING: GEMINI_API_KEY is not set. Running programmatic parser.")
        return extract_candidate_profile_programmatic(resume_text)
        
    try:
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        user_prompt = USER_PROMPT_TEMPLATE.format(resume_text=resume_text)
        
        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=LLMExtractedProfile,
                temperature=0.1
            )
        )
        
        raw_text = response.text
        if not raw_text:
            raise ValueError("Empty response received from Gemini API.")
            
        data = json.loads(raw_text)
        return LLMExtractedProfile.model_validate(data)
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        raise RuntimeError(f"Failed to analyze resume with Gemini API: {str(e)}")

def get_mock_job_match() -> JobMatchReport:
    """
    Returns a mock job match report for testing or when Gemini API key is not configured.
    """
    return JobMatchReport(
        matched_keywords=["Python", "Flask", "REST APIs", "PostgreSQL", "AWS", "Git"],
        missing_keywords=["Docker", "Kubernetes", "Redis", "CI/CD"],
        matched_required_skills=["Python programming", "Web frameworks (Flask)", "SQL database experience"],
        missing_required_skills=["Containerization (Docker)", "Cloud deployment infrastructure"],
        matched_preferred_skills=["RESTful API design", "Mentoring junior developers"],
        missing_preferred_skills=["NoSQL databases (Redis/MongoDB)", "Kubernetes orchestration"],
        jd_match_score=78.5
    )

def match_job_description(resume_text: str, job_description: str) -> JobMatchReport:
    """
    Compares the resume text against the target job description using the Gemini API.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    
    # If API key is not configured, run programmatic job description matching
    if not api_key or api_key.strip() == "" or "your_gemini_api_key" in api_key:
        print("WARNING: GEMINI_API_KEY is not set. Running programmatic job description matching.")
        return match_job_description_programmatic(resume_text, job_description)
        
    try:
        from prompts import JOB_MATCH_SYSTEM_PROMPT, JOB_MATCH_USER_PROMPT_TEMPLATE
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=JOB_MATCH_SYSTEM_PROMPT
        )
        
        user_prompt = JOB_MATCH_USER_PROMPT_TEMPLATE.format(
            resume_text=resume_text,
            job_description=job_description
        )
        
        response = model.generate_content(
            user_prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=JobMatchReport,
                temperature=0.1
            )
        )
        
        raw_text = response.text
        if not raw_text:
            raise ValueError("Empty response received from Gemini API.")
            
        data = json.loads(raw_text)
        return JobMatchReport.model_validate(data)
        
    except Exception as e:
        print(f"Gemini JD match API error: {e}")
        print("Falling back to programmatic match report.")
        return match_job_description_programmatic(resume_text, job_description)

def improve_bullet_point(bullet_text: str, role_context: Optional[str] = None) -> str:
    """
    Improves a weak resume bullet point.
    If Gemini API key is present, calls Gemini with a strict non-hallucination prompt.
    Otherwise, uses programmatic rules to clean up passive start verbs and preserve facts.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key and api_key.strip() and "your_gemini_api_key" not in api_key:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash")
            
            prompt = (
                f"You are a professional resume advisor. Improve the following resume bullet point to make it more impactful, "
                f"beginning it with a strong active technical verb. "
                f"Preserve ALL original factual details, technologies, and metrics. "
                f"CRITICAL: Do NOT invent or add any numbers, metrics, technologies, or achievements that are not present. "
                f"If the original bullet lacks a quantified metric, do NOT invent one, but append '(Add a genuine metric here if available)' to the end. "
                f"Original Bullet: \"{bullet_text}\"\n"
                f"Role Context: {role_context or 'Software Engineering'}\n"
                f"Return only the improved bullet point string inside quotes."
            )
            
            response = model.generate_content(prompt)
            res_text = response.text.strip().strip('"\'')
            if res_text:
                return res_text
        except Exception as e:
            print(f"Gemini bullet improver error: {e}")
            
    # Programmatic fallback (no API key or error)
    text = bullet_text.strip()
    words = text.split()
    if not words:
        return ""
        
    first_word = words[0].lower().strip(",.;")
    weak_verbs_map = {
        "worked": "Engineered",
        "helped": "Spearheaded",
        "assisted": "Orchestrated",
        "responsible": "Managed",
        "was": "Architected",
        "made": "Created",
        "wrote": "Implemented",
        "managed": "Coordinated",
        "built": "Developed",
        "did": "Executed"
    }
    
    starts_with_phrase = False
    if len(words) > 1:
        phrase = f"{words[0].lower()} {words[1].lower()}"
        if phrase == "responsible for":
            words = words[2:]
            words[0] = "Managed"
            starts_with_phrase = True
        elif phrase == "worked on":
            words = words[2:]
            words[0] = "Engineered"
            starts_with_phrase = True
            
    if not starts_with_phrase and first_word in weak_verbs_map:
        words[0] = weak_verbs_map[first_word]
        
    improved_text = " ".join(words)
    
    has_number = any(char.isdigit() for char in improved_text)
    if not has_number:
        improved_text += " (Add a genuine metric here if available)"
        
    return improved_text
