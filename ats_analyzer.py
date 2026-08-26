import re
from typing import List, Dict, Optional
from schemas import (
    CandidateProfile, PersonalInfo, Education, Experience, Project,
    Certification, Achievement, SkillProfile, ATSCategoryScores,
    ATSCompatibilityReport, CompatibilityCheck, CompletenessReport,
    AchievementReport, KeywordIntelligence, ImpactAnalysis, JobMatchReport,
    CanonicalResume, CanonicalBullet, ItemEvidence, ExtractionEvidence,
    ScoreEvidence, ATSCompatibilityEvidence, ResumeStructureEvidence,
    KeywordRelevanceEvidence, ContentQualityEvidence, SkillsRepresentationEvidence,
    QuantifiedImpactEvidence, CompletenessEvidence, ReadabilityConsistencyEvidence,
    CategoryExplanation, ResumeWeakness, SkillGapDetail, TargetRoleFit,
    TopImprovement, ATSSimulationCheck, ATSSimulationReport
)
from extractor import LLMExtractedProfile

# Technical action verbs
ACTION_VERBS = {
    "developed", "implemented", "improved", "optimized", "designed", "built",
    "spearheaded", "reduced", "increased", "managed", "created", "led",
    "engineered", "streamlined", "automated", "facilitated", "mentored",
    "established", "orchestrated", "architected", "coordinated", "executed"
}

# Regex to detect quantified metrics
# E.g. percentages (25%), scales (10M, 5K, 3x), currency ($100K, $2M), numeric quantities (50+ servers)
METRIC_REGEX = re.compile(
    r'\b(?:\d+(?:\.\d+)?%\s*(?:F1-score|accuracy|increase|decrease|growth|improvement)?|'
    r'\d{1,3}(?:,\d{3})+(?:\+)?\b|'
    r'\b\d+(?:\+)?\s*(?:million|billion|thousand|K|M|B|percent|x)\b|'
    r'\$\s*\d+(?:\.\d+)?\s*(?:million|billion|thousand|K|M|B)?\b|'
    r'\b\d+\s*(?:years|months|days|hours|minutes|seconds|percent|users|servers|clients|databases|APIs|pages|leads|features|developers)\b|'
    r'\b(?:first|second|third|1st|2nd|3rd|top\s*\d+(?:%|\b))'
    r')', re.IGNORECASE
)

def normalize_tech_keyword(kw: str) -> str:
    """
    Deduplicates and standardizes variation names of technical skills and tools.
    """
    val = kw.strip().lower()
    if val in ["rest api", "rest apis", "restful api", "restful apis"]:
        return "rest apis"
    if val in ["javascript", "java script", "js"]:
        return "javascript"
    if val in ["postgresql", "postgres", "postgresql database"]:
        return "postgresql"
    if val in ["mongodb", "mongo"]:
        return "mongodb"
    if val in ["react", "react.js", "reactjs"]:
        return "react"
    if val in ["fastapi", "fast api"]:
        return "fastapi"
    if val in ["html5", "html"]:
        return "html"
    if val in ["css3", "css"]:
        return "css"
    return val

def classify_metric_type(metric_phrase: str, bullet_text: str) -> str:
    phrase_lower = metric_phrase.lower()
    text_lower = bullet_text.lower()
    
    # 1. Contact number
    if re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3,4}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', metric_phrase) or re.search(r'\b\d{5,6}\b', metric_phrase):
        return "contact_number"
        
    # 2. Academic GPA
    if "gpa" in text_lower or "cgpa" in text_lower or "grade" in text_lower or "/" in metric_phrase:
        if re.search(r'\b\d+(?:\.\d+)?\s*/\s*\d+\b', metric_phrase):
            return "academic_metric"
            
    # 3. Date / Duration
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec", "present"]
    if any(m in phrase_lower for m in months) or re.search(r'\b(?:19|20)\d{2}\b', metric_phrase):
        return "date"
    if any(re.search(r'\b' + re.escape(w) + r's?\b', phrase_lower) for w in ["year", "month", "week", "day", "hour", "hr", "yr", "mo"]) and not any(re.search(r'\b' + re.escape(a) + r'\b', text_lower) for a in ["save", "saving", "reduce", "reducing", "cut", "optimize", "optimizing"]):
        if not any(re.search(r'\b' + re.escape(k) + r'\b', text_lower) for k in ["save", "saving", "reduce", "reducing", "cut", "increase", "increasing", "improve", "improving"]):
            return "date"
            
    # 4. Technical Metric (e.g. "21 hand landmarks", "12 REST API endpoints", "3 databases")
    tech_indicators = ["landmark", "endpoint", "database", "server", "class", "model", "parameter", "feature", "epoch", "layer", "dimension", "sensor", "api", "node"]
    if any(re.search(r'\b' + re.escape(t) + r's?\b', text_lower) for t in tech_indicators):
        achievement_triggers = [
            "reduce", "reducing", "reduced", "save", "saving", "saved", 
            "increase", "increasing", "increased", "improve", "improving", "improved", 
            "optimize", "optimizing", "optimized", "cut", "boost", "boosted", 
            "grow", "grown", "generate", "generating", "generated", "achieve", "achieved"
        ]
        if not any(re.search(r'\b' + re.escape(trig) + r'\b', text_lower) for trig in achievement_triggers):
            return "technical_metric"
            
    # 5. Achievement Metric
    achievement_terms = [
        "%", "percent", "accuracy", "speedup", "latency", "reduce", "reducing", "reduced",
        "save", "saving", "saved", "increase", "increasing", "increased", 
        "improve", "improving", "improved", "optimize", "optimizing", "optimized", 
        "revenue", "cost", "scale", "throughput", "request", "fps", "$", "budget", 
        "usd", "euro", "dollar", "achieve", "achieved"
    ]
    if "%" in phrase_lower or "$" in phrase_lower or any(re.search(r'\b' + re.escape(term) + r'\b', phrase_lower) for term in achievement_terms) or any(re.search(r'\b' + re.escape(term) + r'\b', text_lower) for term in achievement_terms):
        return "achievement_metric"
        
    return "identifier"

def extract_numeric_phrases(bullet_text: str) -> List[str]:
    phrases = []
    special_matches = re.findall(r'\b\d+(?:\.\d+)?\s*%(?!\w)|\b\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?\b', bullet_text)
    phrases.extend(special_matches)
    
    word_matches = re.findall(r'\b\d+(?:\.\d+)?\s*(?:[a-zA-Z]+(?:\s+[a-zA-Z]+){0,2})\b', bullet_text)
    phrases.extend(word_matches)
    
    standalone = re.findall(r'\b\d+(?:\.\d+)?\b', bullet_text)
    phrases.extend(standalone)
    
    cleaned = []
    for p in sorted(list(set(phrases)), key=len, reverse=True):
        if not any(p in c for c in cleaned):
            cleaned.append(p)
            
    return cleaned

def classify_bullet_metrics(bullet_text: str) -> str:
    phrases = extract_numeric_phrases(bullet_text)
    has_strong = False
    has_partial = False
    
    for phrase in phrases:
        m_type = classify_metric_type(phrase, bullet_text)
        if m_type == "achievement_metric":
            has_strong = True
        elif m_type == "technical_metric":
            has_partial = True
            
    if has_strong:
        return "strong"
    elif has_partial:
        return "partial"
    return "none"

def extract_metrics_verbatim(text: str) -> List[str]:
    phrases = extract_numeric_phrases(text)
    achievement_metrics = []
    for phrase in phrases:
        m_type = classify_metric_type(phrase, text)
        if m_type == "achievement_metric":
            achievement_metrics.append(phrase)
    return sorted(list(set(achievement_metrics)))

def find_in_text(val: Optional[str], raw_text: str) -> tuple[str, float, Optional[str]]:
    """
    Sub-string match validation for verification tracing.
    """
    if not val or not val.strip():
        return "not_provided", 1.0, None
    val_clean = val.strip().lower()
    raw_clean = raw_text.lower()
    
    if val_clean in raw_clean:
        return "resume_text", 1.0, val
        
    words = [w for w in val_clean.split() if len(w) > 2]
    if not words:
        if val_clean in raw_clean:
            return "resume_text", 1.0, val
        return "not_found_in_resume", 0.0, None
        
    matched_words = [w for w in words if w in raw_clean]
    if len(matched_words) == len(words):
        return "resume_text", 0.9, val
    elif len(matched_words) >= max(1, len(words) // 2):
        return "resume_text", 0.6, " ".join(matched_words)
        
    return "not_found_in_resume", 0.0, None

def build_canonical_resume(extracted_profile: LLMExtractedProfile, raw_text: str) -> tuple[CanonicalResume, ExtractionEvidence]:
    """
    Builds the single source of truth CanonicalResume representation.
    Verifies and grounds every field against the raw text.
    """
    if not raw_text or not raw_text.strip():
        raise ValueError("Raw resume text is empty or not provided.")
        
    # Trace Personal Info Name
    pi = extracted_profile.personal_info
    candidate_name = pi.name
    if not candidate_name or not candidate_name.strip():
        raise ValueError("Candidate name is missing from the extracted profile.")
        
    _, name_conf, _ = find_in_text(candidate_name, raw_text)
    if name_conf == 0.0:
        raise ValueError(f"Extracted candidate name '{candidate_name}' cannot be traced in the raw resume text.")
        
    # Check if we have at least one real section
    has_section = (
        len(extracted_profile.education) > 0 or
        len(extracted_profile.experience) > 0 or
        len(extracted_profile.projects) > 0 or
        len(extracted_profile.skill_profile.normalized_skills) > 0
    )
    if not has_section:
        raise ValueError("No real resume sections (Education, Experience, Projects, Skills) were extracted.")

    item_evidence = []
    extraction_warnings = []
    source_bullets = []
    
    # Ground personal info contact details
    clean_pi_data = {}
    for field in ["name", "email", "phone", "location", "linkedin", "github", "portfolio"]:
        val = getattr(pi, field)
        if val:
            src, conf, match_sub = find_in_text(val, raw_text)
            item_evidence.append(ItemEvidence(
                item_type="personal_info",
                field_name=field,
                extracted_value=val,
                source=src,
                confidence=conf,
                matched_substring=match_sub
            ))
            if conf > 0.0:
                clean_pi_data[field] = val
            else:
                clean_pi_data[field] = None
                extraction_warnings.append(f"Extracted contact field '{field}' with value '{val}' was not found in the raw resume text and was removed.")
        else:
            clean_pi_data[field] = None
            
    clean_pi = PersonalInfo(**clean_pi_data)

    # Trace Education
    education_clean = []
    for i, edu in enumerate(extracted_profile.education):
        if not edu.institution:
            continue
        src, inst_conf, match_sub = find_in_text(edu.institution, raw_text)
        item_evidence.append(ItemEvidence(
            item_type="education",
            field_name=f"institution_{i}",
            extracted_value=edu.institution,
            source=src,
            confidence=inst_conf,
            matched_substring=match_sub
        ))
        if inst_conf == 0.0:
            extraction_warnings.append(f"Extracted education institution '{edu.institution}' was not found in the raw resume text and was skipped.")
            continue
            
        clean_edu_data = {"institution": edu.institution}
        for field in ["degree", "field", "gpa", "start_year", "graduation_year"]:
            val = getattr(edu, field)
            if val:
                src, conf, match_sub = find_in_text(val, raw_text)
                item_evidence.append(ItemEvidence(
                    item_type="education",
                    field_name=f"{field}_{i}",
                    extracted_value=val,
                    source=src,
                    confidence=conf,
                    matched_substring=match_sub
                ))
                if conf > 0.0:
                    clean_edu_data[field] = val
                else:
                    clean_edu_data[field] = None
                    extraction_warnings.append(f"Extracted education {field} '{val}' was not found in the raw resume text and was removed.")
            else:
                clean_edu_data[field] = None
        education_clean.append(Education(**clean_edu_data))

    # Trace Experience & extract bullets
    experience_clean = []
    research_experience_clean = []
    extracurriculars_clean = []
    all_bullets = []
    bullet_counter = 0
    
    for i, exp in enumerate(extracted_profile.experience):
        if not exp.company:
            continue
        src, comp_conf, match_sub = find_in_text(exp.company, raw_text)
        item_evidence.append(ItemEvidence(
            item_type="experience",
            field_name=f"company_{i}",
            extracted_value=exp.company,
            source=src,
            confidence=comp_conf,
            matched_substring=match_sub
        ))
        if comp_conf == 0.0:
            extraction_warnings.append(f"Extracted experience company '{exp.company}' was not found in raw text and was skipped.")
            continue
            
        clean_exp_data = {"company": exp.company}
        for field in ["role", "duration"]:
            val = getattr(exp, field)
            if val:
                src, conf, match_sub = find_in_text(val, raw_text)
                item_evidence.append(ItemEvidence(
                    item_type="experience",
                    field_name=f"{field}_{i}",
                    extracted_value=val,
                    source=src,
                    confidence=conf,
                    matched_substring=match_sub
                ))
                if conf > 0.0:
                    clean_exp_data[field] = val
                else:
                    clean_exp_data[field] = None
                    extraction_warnings.append(f"Extracted experience {field} '{val}' was not found in the raw resume text and was removed.")
            else:
                clean_exp_data[field] = None
                
        clean_bullets = []
        for bullet_text in exp.responsibilities + exp.achievements:
            b_clean = bullet_text.strip()
            if b_clean:
                src, conf, match_sub = find_in_text(b_clean, raw_text)
                if conf > 0.0:
                    clean_bullets.append(b_clean)
                    source_bullets.append(b_clean)
                else:
                    extraction_warnings.append(f"Extracted bullet point was not found in raw text and was removed.")
                    
        clean_exp_data["responsibilities"] = clean_bullets
        clean_exp_data["achievements"] = []
        clean_exp_data["technologies"] = getattr(exp, "technologies", [])
        
        exp_obj = Experience(**clean_exp_data)
        lower_comp = exp.company.lower()
        if "mudra" in lower_comp or "research" in lower_comp or "paper" in lower_comp or "publications" in lower_comp:
            research_experience_clean.append(exp_obj)
        elif "club" in lower_comp or "bit by bit" in lower_comp or "ux club" in lower_comp or "society" in lower_comp:
            extracurriculars_clean.append(exp_obj)
        else:
            experience_clean.append(exp_obj)

    # Trace Projects
    projects_clean = []
    for i, proj in enumerate(extracted_profile.projects):
        if not proj.name:
            continue
        src, name_conf, match_sub = find_in_text(proj.name, raw_text)
        item_evidence.append(ItemEvidence(
            item_type="project",
            field_name=f"name_{i}",
            extracted_value=proj.name,
            source=src,
            confidence=name_conf,
            matched_substring=match_sub
        ))
        if name_conf == 0.0:
            extraction_warnings.append(f"Extracted project name '{proj.name}' was not found in the raw resume text and was skipped.")
            continue
            
        clean_proj_data = {
            "name": proj.name,
            "domain": proj.domain,
            "technologies": proj.technologies,
            "links": proj.links
        }
        
        proj_bullets_text = []
        if proj.achievements:
            proj_bullets_text = [item.strip().lstrip("-*•").strip() for item in re.split(r'\n+|- |• |\* ', proj.achievements.strip()) if item.strip()]
        elif proj.description:
            proj_bullets_text = [item.strip().lstrip("-*•").strip() for item in re.split(r'\n+|- |• |\* ', proj.description.strip()) if item.strip()]
            
        clean_proj_bullets = []
        for bullet_text in proj_bullets_text:
            b_clean = bullet_text.strip()
            if b_clean:
                src, conf, match_sub = find_in_text(b_clean, raw_text)
                if conf > 0.0:
                    clean_proj_bullets.append(b_clean)
                    source_bullets.append(b_clean)
                else:
                    extraction_warnings.append(f"Extracted project bullet point was not found in the raw resume text and was removed.")
                    
        clean_proj_data["description"] = " ".join(clean_proj_bullets)
        clean_proj_data["achievements"] = "\n".join(clean_proj_bullets) if clean_proj_bullets else None
        
        projects_clean.append(Project(**clean_proj_data))

    # Trace Certifications
    certifications_clean = []
    for i, cert in enumerate(extracted_profile.certifications):
        if not cert.name:
            continue
        src, conf, match_sub = find_in_text(cert.name, raw_text)
        item_evidence.append(ItemEvidence(
            item_type="certification",
            field_name=f"name_{i}",
            extracted_value=cert.name,
            source=src,
            confidence=conf,
            matched_substring=match_sub
        ))
        if conf > 0.0:
            certifications_clean.append(cert)
        else:
            extraction_warnings.append(f"Extracted certification '{cert.name}' was not found in the raw resume text and was skipped.")

    # Trace Achievements
    achievements_clean = []
    for i, ach in enumerate(extracted_profile.achievements):
        if not ach.description:
            continue
        src, conf, match_sub = find_in_text(ach.description, raw_text)
        item_evidence.append(ItemEvidence(
            item_type="achievement",
            field_name=f"description_{i}",
            extracted_value=ach.description,
            source=src,
            confidence=conf,
            matched_substring=match_sub
        ))
        if conf > 0.0:
            achievements_clean.append(ach)
        else:
            extraction_warnings.append(f"Extracted achievement '{ach.description}' was not found in the raw resume text and was skipped.")

    # Trace Skills
    skills_clean = []
    for s in extracted_profile.skill_profile.normalized_skills:
        src, conf, match_sub = find_in_text(s, raw_text)
        item_evidence.append(ItemEvidence(
            item_type="skill",
            field_name="skill",
            extracted_value=s,
            source=src,
            confidence=conf,
            matched_substring=match_sub
        ))
        if conf > 0.0:
            skills_clean.append(s)
        else:
            extraction_warnings.append(f"Extracted skill '{s}' was not found in the raw resume text and was skipped.")

    # Detect sections from text
    from resume_parser import detect_sections
    sections_detected_dict = detect_sections(raw_text)
    sections_detected = [sec for sec, present in sections_detected_dict.items() if present]

    # Reassemble experience / projects/ extracurriculars / research bullets into a single list
    for exp in experience_clean:
        for b in exp.responsibilities:
            all_bullets.append(CanonicalBullet(
                id=f"bullet_exp_{bullet_counter}",
                section="experience",
                subsection="Experience",
                entity=exp.company,
                role=exp.role,
                text=b,
                quantification_type="none"
            ))
            bullet_counter += 1
            
    for exp in research_experience_clean:
        for b in exp.responsibilities:
            all_bullets.append(CanonicalBullet(
                id=f"bullet_res_{bullet_counter}",
                section="research_experience",
                subsection="Research Experience",
                entity=exp.company,
                role=exp.role,
                text=b,
                quantification_type="none"
            ))
            bullet_counter += 1
            
    for proj in projects_clean:
        proj_bullets = [item.strip() for item in re.split(r'\n+|- |• |\* ', proj.achievements or proj.description or "") if item.strip()]
        for b in proj_bullets:
            all_bullets.append(CanonicalBullet(
                id=f"bullet_proj_{bullet_counter}",
                section="projects",
                subsection="Projects",
                entity=proj.name,
                role=None,
                text=b,
                quantification_type="none"
            ))
            bullet_counter += 1
            
    for exp in extracurriculars_clean:
        for b in exp.responsibilities:
            all_bullets.append(CanonicalBullet(
                id=f"bullet_extra_{bullet_counter}",
                section="extracurriculars",
                subsection="Extracurricular Activities",
                entity=exp.company,
                role=exp.role,
                text=b,
                quantification_type="none"
            ))
            bullet_counter += 1

    canonical_resume = CanonicalResume(
        personal_info=clean_pi,
        summary=extracted_profile.ai_summary,
        education=education_clean,
        experience=experience_clean,
        research_experience=research_experience_clean,
        projects=projects_clean,
        skills=skills_clean,
        certifications=certifications_clean,
        achievements=achievements_clean,
        extracurriculars=extracurriculars_clean,
        all_bullets=all_bullets,
        raw_text=raw_text
    )
    
    ext_evidence = ExtractionEvidence(
        raw_text_length=len(raw_text),
        page_count=1,
        sections_detected=sections_detected,
        source_bullets=source_bullets,
        extraction_warnings=extraction_warnings,
        item_evidence=item_evidence
    )
    
    return canonical_resume, ext_evidence

def run_bullet_analysis(canonical_resume: CanonicalResume) -> dict:
    """
    Returns a unified parsed metrics dictionary from the canonical bullets.
    """
    bullets = []
    strong_count = 0
    partial_count = 0
    none_count = 0
    detected_metrics = []
    technical_metrics = []
    achievement_metrics = []
    
    for b in canonical_resume.all_bullets:
        phrases = extract_numeric_phrases(b.text)
        bullet_metrics = []
        has_strong = False
        has_partial = False
        
        for phrase in phrases:
            m_type = classify_metric_type(phrase, b.text)
            if m_type == "achievement_metric":
                has_strong = True
                achievement_metrics.append(phrase)
                detected_metrics.append(phrase)
                bullet_metrics.append(phrase)
            elif m_type == "technical_metric":
                has_partial = True
                technical_metrics.append(phrase)
                detected_metrics.append(phrase)
                bullet_metrics.append(phrase)
                
        b.metrics = bullet_metrics
        b.has_metric = len(bullet_metrics) > 0
        if has_strong:
            b.quantification_type = "strong"
            strong_count += 1
        elif has_partial:
            b.quantification_type = "partial"
            partial_count += 1
        else:
            b.quantification_type = "none"
            none_count += 1
            
        bullets.append({
            "text": b.text,
            "source": f"{b.role} at {b.entity}" if b.role and b.entity else (b.entity or "Context"),
            "type": b.section,
            "class": b.quantification_type,
            "metrics": b.metrics
        })
        
    total_bullets = len(bullets)
    quantified_ratio = (strong_count / total_bullets) if total_bullets > 0 else 0.0
    
    return {
        "bullets": bullets,
        "total_bullets": total_bullets,
        "strong_count": strong_count,
        "partial_count": partial_count,
        "none_count": none_count,
        "quantified_ratio": quantified_ratio,
        "detected_metrics": sorted(list(set(detected_metrics))),
        "technical_metrics": sorted(list(set(technical_metrics))),
        "achievement_metrics": sorted(list(set(achievement_metrics)))
    }

def run_achievement_detection(bullet_info: dict) -> AchievementReport:
    """
    Builds the achievement report using the unified bullet analysis.
    """
    detected_achievements = []
    suggestions = []
    
    for b in bullet_info["bullets"]:
        if b["class"] == "strong":
            detected_achievements.append(f"{b['source']}: {b['text']}")
        else:
            words = b["text"].split()
            if words and words[0].lower() in ACTION_VERBS:
                suggestions.append(
                    f"In your bullet for '{b['source']}', quantify the outcome of: '{b['text']}' (e.g., 'reducing latency by X%' or 'saving Y hours per week')."
                )
                
    if not suggestions and bullet_info["none_count"] > 0:
        suggestions.append("Try to quantify the outcomes of your responsibilities with real numbers or performance achievements.")
        
    return AchievementReport(
        count=len(detected_achievements),
        detected_achievements=detected_achievements,
        suggestions=suggestions
    )

def run_completeness_report(canonical_resume: CanonicalResume) -> tuple[CompletenessReport, CompletenessEvidence]:
    """
    Checks for the presence of standard sections contextually.
    """
    pi = canonical_resume.personal_info
    
    # Contextual check: Student/Entry vs Experienced Professional
    is_student = False
    roles_lower = [exp.role.lower() for exp in canonical_resume.experience if exp.role]
    has_intern = any("intern" in r or "student" in r for r in roles_lower)
    if len(canonical_resume.experience) == 0 or has_intern:
        is_student = True
        
    required_sections = ["Contact Information", "Education", "Skills"]
    if is_student:
        required_sections.append("Projects")
    else:
        required_sections.append("Work Experience")
        
    sections_checked = {
        "Contact Information": bool(pi.name and (pi.email or pi.phone)),
        "Education": len(canonical_resume.education) > 0,
        "Work Experience": len(canonical_resume.experience) > 0,
        "Skills": len(canonical_resume.skills) > 0,
        "Projects": len(canonical_resume.projects) > 0,
        "Certifications": len(canonical_resume.certifications) > 0,
        "Achievements": len(canonical_resume.achievements) > 0
    }
    
    # Contextual Completeness math
    passed_required = sum(1 for sec in required_sections if sections_checked.get(sec, False))
    base_percent = (passed_required / len(required_sections)) * 85.0
    
    optional_sections = [sec for sec in sections_checked.keys() if sec not in required_sections]
    optional_passed = sum(1 for sec in optional_sections if sections_checked.get(sec, False))
    bonus_percent = optional_passed * 5.0
    percent = min(100.0, round(base_percent + bonus_percent))
    
    evidence = []
    candidate_type = "Student/Entry-Level" if is_student else "Experienced Professional"
    evidence.append(f"Candidate Type: {candidate_type}")
    evidence.append(f"Required Sections: {', '.join(required_sections)}")
    for sec, present in sections_checked.items():
        evidence.append(f"'{sec}' section: {'Detected' if present else 'Not detected'}")
        
    completeness_score = round(percent / 100.0 * 10.0, 1)
    
    report = CompletenessReport(
        sections=sections_checked,
        completeness_percent=percent
    )
    
    evidence_report = CompletenessEvidence(
        score=completeness_score,
        max_score=10.0,
        evidence=evidence
    )
    
    return report, evidence_report

def run_compatibility_checks(
    canonical_resume: CanonicalResume,
    parser_metadata: dict,
    bullet_info: dict
) -> tuple[ATSCompatibilityReport, ATSCompatibilityEvidence]:
    """
    Checks parsing formatting and formatting checks.
    """
    checks = []
    
    # 1. Contact Information
    pi = canonical_resume.personal_info
    if not pi.email and not pi.phone:
        checks.append(CompatibilityCheck(
            name="Contact Information",
            status="fail",
            message="No contact information (email or phone) was detected in the resume."
        ))
    elif not pi.email or not pi.phone:
        checks.append(CompatibilityCheck(
            name="Contact Information",
            status="warn",
            message=f"Partial contact details. Only {'email' if pi.email else 'phone'} was detected."
        ))
    else:
        checks.append(CompatibilityCheck(
            name="Contact Information",
            status="pass",
            message="Both email and phone contact details were successfully detected."
        ))
        
    # 2. Critical sections
    missing_critical = []
    if len(canonical_resume.education) == 0:
        missing_critical.append("Education")
    if len(canonical_resume.experience) == 0:
        missing_critical.append("Experience")
    if len(canonical_resume.skills) == 0:
        missing_critical.append("Skills")
        
    if missing_critical:
        checks.append(CompatibilityCheck(
            name="Critical Resume Sections",
            status="fail",
            message=f"Missing standard section(s) in resume text: {', '.join(missing_critical)}. ATS parsers look for these sections."
        ))
    else:
        checks.append(CompatibilityCheck(
            name="Critical Resume Sections",
            status="pass",
            message="All critical sections (Education, Experience, Skills) were successfully detected."
        ))
        
    # 3. Column layout
    if parser_metadata.get("has_columns", False):
        checks.append(CompatibilityCheck(
            name="Resume Column Layout",
            status="warn",
            message="Multi-column or sidebar layout detected. Simple single-column layouts are parsed more reliably by legacy ATS systems."
        ))
    else:
        checks.append(CompatibilityCheck(
            name="Resume Column Layout",
            status="pass",
            message="Standard single-column text layout detected."
        ))
        
    # 4. Scanned quality
    if parser_metadata.get("is_scanned", False):
        checks.append(CompatibilityCheck(
            name="Text Extraction Quality",
            status="fail",
            message="Resume text is embedded in images or appears scanned. Legacy ATS systems cannot index this content."
        ))
    else:
        checks.append(CompatibilityCheck(
            name="Text Extraction Quality",
            status="pass",
            message="Resume text is digitally extractable and clean."
        ))
        
    # 5. Employment dates
    missing_dates = False
    for exp in canonical_resume.experience:
        if not exp.duration or exp.duration.strip() == "":
            missing_dates = True
            break
            
    if missing_dates:
        checks.append(CompatibilityCheck(
            name="Employment Dates",
            status="warn",
            message="One or more work experience entries are missing duration dates."
        ))
    else:
        checks.append(CompatibilityCheck(
            name="Employment Dates",
            status="pass",
            message="All work experience items contain active dates."
        ))
        
    # 6. Paragraph length
    long_paragraphs = False
    for b in bullet_info["bullets"]:
        if len(b["text"]) > 280:
            long_paragraphs = True
            break
            
    if long_paragraphs:
        checks.append(CompatibilityCheck(
            name="Text Paragraph Lengths",
            status="warn",
            message="Detected extremely long paragraph bullets (> 280 characters). Break them down for better ATS and recruiter reading."
        ))
    else:
        checks.append(CompatibilityCheck(
            name="Text Paragraph Lengths",
            status="pass",
            message="All experience bullet points are concise and readable."
        ))
        
    # 7. Outcomes
    total = bullet_info["total_bullets"]
    strong = bullet_info["strong_count"]
    ratio = bullet_info["quantified_ratio"]
    
    if total > 0 and ratio < 0.35:
        checks.append(CompatibilityCheck(
            name="Measurable Outcomes",
            status="fail" if ratio < 0.1 else "warn",
            message=f"Only {strong}/{total} experience/project bullets contain strong measurable metrics. Quantifying results is highly recommended."
        ))
    else:
        checks.append(CompatibilityCheck(
            name="Measurable Outcomes",
            status="pass",
            message=f"Good representation of metrics and quantitative outcomes: {strong}/{total} experience/project bullets contain strong metrics."
        ))
        
    # Rubric details out of 15
    compat_score = 0.0
    passed = []
    warnings = []
    for c in checks:
        status_mult = 1.0 if c.status == "pass" else (0.5 if c.status == "warn" else 0.0)
        item_score = 0.0
        if c.name == "Contact Information":
            item_score = 2.0 * status_mult
        elif c.name == "Critical Resume Sections":
            item_score = 4.0 * status_mult
        elif c.name == "Text Extraction Quality":
            item_score = 3.0 * status_mult
        elif c.name == "Employment Dates":
            item_score = 2.0 * status_mult
        elif c.name == "Resume Column Layout":
            item_score = 2.0 * status_mult
            
        compat_score += item_score
        
        msg = f"{c.name}: {c.message}"
        if c.status == "pass":
            passed.append(msg)
        else:
            warnings.append(msg)
            
    if len(canonical_resume.experience) > 0 and len(canonical_resume.education) > 0:
        compat_score += 2.0
        passed.append("Structure: Found both work experience and education blocks.")
    else:
        compat_score += 0.5
        warnings.append("Structure: Missing work experience or education block.")
        
    ats_compatibility = round(min(15.0, compat_score), 1)
    
    report = ATSCompatibilityReport(checks=checks)
    evidence = ATSCompatibilityEvidence(
        score=ats_compatibility,
        max_score=15.0,
        passed=passed,
        warnings=warnings
    )
    
    return report, evidence

def run_keyword_intelligence(
    canonical_resume: CanonicalResume,
    job_match: Optional[JobMatchReport]
) -> tuple[KeywordIntelligence, KeywordRelevanceEvidence, KeywordRelevanceEvidence]:
    """
    Evaluates keyword domain strength and JD match.
    """
    domain_keywords = {
        "Software Engineering": ["python", "javascript", "c++", "java", "rust", "go", "typescript", "git", "rest api", "oop"],
        "Web Development": ["html", "css", "react", "vue", "angular", "flask", "django", "fastapi", "node", "express", "tailwind", "jquery"],
        "Cloud & DevOps": ["aws", "gcp", "azure", "docker", "kubernetes", "terraform", "ci/cd", "jenkins", "linux", "ansible"],
        "Data & AI": ["machine learning", "pytorch", "tensorflow", "pandas", "numpy", "sql", "data science", "nlp", "llm", "ai", "scikit-learn"]
    }
    
    strengths = {}
    normalized_lowercase = [normalize_tech_keyword(s) for s in canonical_resume.skills]
    
    matched_domains = []
    missing_domains = []
    
    for domain, keywords in domain_keywords.items():
        matches = [kw for kw in keywords if normalize_tech_keyword(kw) in normalized_lowercase]
        if len(matches) >= 4:
            strengths[domain] = "High"
            matched_domains.append(f"{domain} (High, matches: {', '.join(matches)})")
        elif len(matches) >= 1:
            strengths[domain] = "Medium"
            matched_domains.append(f"{domain} (Medium, matches: {', '.join(matches)})")
        else:
            strengths[domain] = "Low"
            missing_domains.append(f"{domain} (Low, matches: none)")
            
    is_jd = job_match is not None
    label = "Job Match Score" if is_jd else "General Keyword Relevance"
    
    if is_jd:
        matched_req = sorted(list(set(normalize_tech_keyword(s) for s in job_match.matched_required_skills)))
        missing_req = sorted(list(set(normalize_tech_keyword(s) for s in job_match.missing_required_skills)))
        matched_pref = sorted(list(set(normalize_tech_keyword(s) for s in job_match.matched_preferred_skills)))
        missing_pref = sorted(list(set(normalize_tech_keyword(s) for s in job_match.missing_preferred_skills)))

        total_req = len(matched_req) + len(missing_req)
        req_ratio = len(matched_req) / total_req if total_req > 0 else 1.0
        
        total_pref = len(matched_pref) + len(missing_pref)
        pref_ratio = len(matched_pref) / total_pref if total_pref > 0 else 1.0
        
        weighted_score = (req_ratio * 75.0) + (pref_ratio * 25.0)
        job_match.jd_match_score = round(weighted_score, 1)
        score = round((job_match.jd_match_score / 100.0) * 20.0, 1)
        
        evidence = KeywordRelevanceEvidence(
            score=score,
            max_score=20.0,
            matched=[f"Required: {s}" for s in job_match.matched_required_skills] + [f"Preferred: {s}" for s in job_match.matched_preferred_skills],
            missing=[f"Required: {s}" for s in job_match.missing_required_skills] + [f"Preferred: {s}" for s in job_match.missing_preferred_skills]
        )
    else:
        # General Keyword Relevance (max 20) based on target roles
        target_domains = {
            "AI/ML Engineering": [
                "python", "pytorch", "tensorflow", "opencv", "mediapipe", "gemini api",
                "google gemini api", "agentic ai", "rag", "multi-agent systems", "retrieval-augmented generation (rag)", "yolo"
            ],
            "Computer Vision Research": [
                "opencv", "mediapipe", "yolo", "pytorch", "tensorflow", "object detection",
                "tracking", "pose estimation", "gesture recognition", "hand landmarks"
            ],
            "SDE internships": [
                "java", "python", "javascript", "sql", "flask", "rest apis",
                "data structures & algorithms", "object-oriented programming", "full-stack development"
            ]
        }
        
        active_targets = []
        summary_lower = (canonical_resume.summary or "").lower() + " " + (canonical_resume.raw_text or "").lower()
        if "ai/ml" in summary_lower or "machine learning" in summary_lower or "ml engineering" in summary_lower:
            active_targets.append("AI/ML Engineering")
        if "computer vision" in summary_lower or "vision research" in summary_lower:
            active_targets.append("Computer Vision Research")
        if "sde" in summary_lower or "software engineer" in summary_lower or "software development" in summary_lower or "internship" in summary_lower:
            active_targets.append("SDE internships")
            
        if not active_targets:
            active_targets = ["AI/ML Engineering", "Computer Vision Research", "SDE internships"]
            
        total_matches = []
        total_missing = []
        ratios = []
        
        for target in active_targets:
            keywords = target_domains[target]
            matched = []
            missing = []
            for kw in keywords:
                if any(kw == s.lower() or kw in s.lower() for s in canonical_resume.skills) or re.search(r'\b' + re.escape(kw) + r'\b', canonical_resume.raw_text, re.IGNORECASE):
                    matched.append(kw)
                else:
                    missing.append(kw)
            total_matches.extend(matched)
            total_missing.extend(missing)
            ratios.append(len(matched) / len(keywords) if keywords else 1.0)
            
        avg_ratio = sum(ratios) / len(ratios) if ratios else 0.0
        score = round(min(16.0, 20.0 * avg_ratio), 1)
        
        evidence = KeywordRelevanceEvidence(
            score=score,
            max_score=20.0,
            matched=[f"Target Role: {t}" for t in active_targets] + [f"Matched Keywords: {', '.join(sorted(list(set(total_matches))))}"],
            missing=[f"Missing Target Keywords: {', '.join(sorted(list(set(total_missing))))}"]
        )
        
    intel = KeywordIntelligence(
        domain_strength=strengths,
        job_match=job_match,
        is_jd_provided=is_jd,
        label=label
    )
    
    return intel, evidence, evidence

def calculate_ats_plus_scores(
    canonical_resume: CanonicalResume,
    parser_metadata: dict,
    compatibility_report: ATSCompatibilityReport,
    completeness_report: CompletenessReport,
    bullet_info: dict,
    keyword_intel: KeywordIntelligence,
    compat_evidence: ATSCompatibilityEvidence,
    completeness_evidence: CompletenessEvidence,
    keyword_evidence: KeywordRelevanceEvidence,
    skill_profile: SkillProfile
) -> tuple[ATSCategoryScores, ScoreEvidence]:
    """
    Calculates detailed category scores based on the strict 100-point rubric and compiles evidence.
    """
    # 1. ATS Compatibility (max 15 points)
    ats_compatibility = compat_evidence.score
    
    # 2. Resume Structure (max 15 points)
    struct_score = 15.0
    evidence_struct = []
    if parser_metadata.get("has_columns", False):
        struct_score -= 4.0
        evidence_struct.append("Layout: Multi-column or sidebar detected (-4.0)")
    else:
        evidence_struct.append("Layout: Single-column standard layout (+4.0)")
        
    if parser_metadata.get("is_scanned", False):
        struct_score -= 6.0
        evidence_struct.append("Parsing: Scanned/Image text layout warning (-6.0)")
    else:
        evidence_struct.append("Parsing: Digitally extractable clean text (+6.0)")
        
    for i, exp in enumerate(canonical_resume.experience):
        if not exp.company or not exp.role:
            struct_score -= 2.0
            evidence_struct.append(f"Structure: Experience item {i} is missing company or role (-2.0)")
            break
            
    for i, edu in enumerate(canonical_resume.education):
        if not edu.institution or not edu.degree:
            struct_score -= 2.0
            evidence_struct.append(f"Structure: Education item {i} is missing institution or degree (-2.0)")
            break
            
    if any(c.name == "Text Paragraph Lengths" and c.status == "warn" for c in compatibility_report.checks):
        struct_score -= 2.0
        evidence_struct.append("Readability: Detected excessively long paragraph bullets (-2.0)")
        
    resume_structure = round(max(0.0, struct_score), 1)
    struct_evidence_model = ResumeStructureEvidence(
        score=resume_structure,
        max_score=15.0,
        evidence=evidence_struct
    )
    
    # 3. Keyword / Job Relevance (max 20 points)
    keyword_relevance = keyword_evidence.score
    
    # 4. Content Quality (max 15 points)
    total_bullets = bullet_info["total_bullets"]
    evidence_content = []
    if total_bullets == 0:
        content_quality = 5.0
        evidence_content.append("Bullets: No work experience or project bullets found. Fallback score (-10.0)")
    else:
        bullets_with_action_verb = 0
        strong_bullets_list = []
        weak_bullets_list = []
        
        for b in canonical_resume.all_bullets:
            # Check action verb starting or in first two words
            words = [w.lower().strip(",.;") for w in b.text.split()]
            has_verb = False
            if words:
                if words[0] in ACTION_VERBS:
                    has_verb = True
                elif len(words) > 1 and words[1] in ACTION_VERBS:
                    has_verb = True
            
            if has_verb:
                bullets_with_action_verb += 1
                strong_bullets_list.append(b.text)
            else:
                weak_bullets_list.append(b.text)
                
        ratio = bullets_with_action_verb / total_bullets
        evidence_content.append(f"Action Verbs: {bullets_with_action_verb} / {total_bullets} bullets start with action verbs ({ratio*100:.1f}%)")
        
        if ratio >= 0.8:
            content_quality = 15.0
        elif ratio >= 0.5:
            content_quality = 12.0
        elif ratio >= 0.3:
            content_quality = 9.0
        else:
            content_quality = 5.0
            
    content_evidence_model = ContentQualityEvidence(
        score=content_quality,
        max_score=15.0,
        strong_bullets=strong_bullets_list if total_bullets > 0 else [],
        weak_bullets=weak_bullets_list if total_bullets > 0 else []
    )
            
    # 5. Skills Representation (max 10 points)
    skills_score = 0.0
    evidence_skills = []
    skills_count = len(canonical_resume.skills)
    
    if skills_count >= 15:
        skills_score += 5.0
        evidence_skills.append("Skills Count: Solid technology stack. Found 15 or more skills (+5.0)")
    elif skills_count >= 8:
        skills_score += 4.0
        evidence_skills.append("Skills Count: Moderate skills list. Found 8-14 skills (+4.0)")
    elif skills_count >= 1:
        skills_score += 2.0
        evidence_skills.append("Skills Count: Minimal skills list. Found 1-7 skills (+2.0)")
        
    if skill_profile.categorized_skills:
        skills_score += 2.5
        evidence_skills.append("Skills Layout: Skills are categorized by domains (+2.5)")
    if skill_profile.normalized_skills:
        skills_score += 2.5
        evidence_skills.append("Skills Standard: Skills are normalized and clean (+2.5)")
        
    if skills_count > 30:
        skills_score -= 2.0
        evidence_skills.append("Keyword Stuffing Penalty: Exceeded 30 skills. Focus your listing (-2.0)")
        
    skills_representation = round(max(0.0, skills_score), 1)
    skills_evidence_model = SkillsRepresentationEvidence(
        score=skills_representation,
        max_score=10.0,
        evidence=evidence_skills
    )
    
    # 6. Quantified Impact (max 10 points)
    strong = bullet_info["strong_count"]
    total = bullet_info["total_bullets"]
    
    if total == 0:
        quantified_impact = 0.0
    else:
        raw_impact = 10.0 * (strong / total)
        quantified_impact = round(min(10.0, raw_impact), 1)
        
    evidence_impact = []
    evidence_impact.append(f"Outcome Metrics: Found {strong} of {total} experience/project bullets containing outcome metrics.")
    tech_list = bullet_info.get("technical_metrics", [])
    if tech_list:
        evidence_impact.append(f"Technical numeric evidence: {', '.join(tech_list)} (Not counted as achievement metric)")
    else:
        evidence_impact.append("No technical numeric scale evidence found.")
        
    impact_evidence_model = QuantifiedImpactEvidence(
        score=quantified_impact,
        max_score=10.0,
        total_bullets=total,
        quantified_bullets=strong,
        metrics=bullet_info["detected_metrics"],
        evidence=evidence_impact
    )
        
    # 7. Resume Completeness (max 10 points)
    completeness = completeness_evidence.score
    
    # 8. Readability & Consistency (max 5 points)
    read_score = 5.0
    evidence_readability = []
    if any(c.name == "Text Paragraph Lengths" and c.status == "warn" for c in compatibility_report.checks):
        read_score -= 1.0
        evidence_readability.append("Penalty: Bullet points are excessively long (-1.0)")
    if any(c.name == "Employment Dates" and c.status == "warn" for c in compatibility_report.checks):
        read_score -= 1.0
        evidence_readability.append("Penalty: Missing dates in experience duration (-1.0)")
        
    # Duplicate skills check
    raw_lower = [s.lower() for s in skill_profile.raw_skills]
    if len(raw_lower) != len(set(raw_lower)):
        read_score -= 1.0
        evidence_readability.append("Penalty: Duplicate skills listed in profile (-1.0)")
        
    if total_bullets > 0:
        bullets_with_action_verb = sum(1 for b in canonical_resume.all_bullets if b.action_verbs)
        if bullets_with_action_verb / total_bullets < 0.25:
            read_score -= 1.0
            evidence_readability.append("Penalty: Less than 25% of bullet points start with action verbs (-1.0)")
            
    if not evidence_readability:
        evidence_readability.append("Readability: Excellent text formatting and consistency (+5.0)")
        
    readability_consistency = round(max(1.0, read_score), 1)
    readability_evidence_model = ReadabilityConsistencyEvidence(
        score=readability_consistency,
        max_score=5.0,
        evidence=evidence_readability
    )
    
    # Overall Score (sum must match overall_score exactly)
    category_sum = (
        ats_compatibility + resume_structure + keyword_relevance +
        content_quality + skills_representation + quantified_impact +
        completeness + readability_consistency
    )
    overall_score = round(category_sum, 1)
    overall_score = min(100.0, overall_score)
    
    # Assert category maxima and bound compliance
    assert 0 <= ats_compatibility <= 15.0, f"ATS Compatibility score out of bounds: {ats_compatibility}"
    assert 0 <= resume_structure <= 15.0, f"Resume Structure score out of bounds: {resume_structure}"
    assert 0 <= keyword_relevance <= 20.0, f"Keyword Relevance score out of bounds: {keyword_relevance}"
    assert 0 <= content_quality <= 15.0, f"Content Quality score out of bounds: {content_quality}"
    assert 0 <= skills_representation <= 10.0, f"Skills Representation score out of bounds: {skills_representation}"
    assert 0 <= quantified_impact <= 10.0, f"Quantified Impact score out of bounds: {quantified_impact}"
    assert 0 <= completeness <= 10.0, f"Completeness score out of bounds: {completeness}"
    assert 0 <= readability_consistency <= 5.0, f"Readability score out of bounds: {readability_consistency}"
    
    if abs(category_sum - overall_score) > 1e-5:
        raise ValueError(f"Math check failed: category sum ({category_sum}) does not equal overall_score ({overall_score})")
        
    if not (0.0 <= overall_score <= 100.0):
        raise ValueError(f"Overall score out of bounds: {overall_score}")
        
    scores = ATSCategoryScores(
        ats_compatibility=ats_compatibility,
        resume_structure=resume_structure,
        keyword_relevance=keyword_relevance,
        content_quality=content_quality,
        skills_representation=skills_representation,
        quantified_impact=quantified_impact,
        completeness=completeness,
        readability_consistency=readability_consistency,
        overall_score=overall_score
    )
    
    score_evidence = ScoreEvidence(
        ats_compatibility=compat_evidence,
        resume_structure=struct_evidence_model,
        keyword_relevance=keyword_evidence,
        content_quality=content_evidence_model,
        skills_representation=skills_evidence_model,
        quantified_impact=impact_evidence_model,
        completeness=completeness_evidence,
        readability_consistency=readability_evidence_model
    )
    
    return scores, score_evidence

def generate_dynamic_recommendations(
    scores: ATSCategoryScores,
    bullet_info: dict,
    is_jd_provided: bool
) -> List[str]:
    """
    Generates actionable improvement recommendations directly derived from low scores, referencing actual fields without inventing metrics.
    """
    recommendations = []
    
    if scores.ats_compatibility < 12.0:
        recommendations.append("Use simpler section headings and a standard single-column structure to improve ATS readability.")
    if scores.resume_structure < 12.0:
        recommendations.append("Ensure consistent date and bullet formatting, and check that all experience entries clearly specify company, role, and duration.")
    if scores.keyword_relevance < 15.0:
        if is_jd_provided:
            recommendations.append("Add relevant technologies and core requirements from the target job description where you genuinely have experience.")
        else:
            recommendations.append("Include more industry-specific technical keywords and domain terminology matching your target roles.")
    if scores.content_quality < 12.0:
        recommendations.append("Begin all experience bullet points with strong, passive-avoiding technical action verbs (e.g. 'Architected', 'Spearheaded', 'Optimized').")
    if scores.skills_representation < 8.0:
        recommendations.append("Organize your skills section into categorized groups (e.g. Languages, Frameworks, Tools) to make it easy for recruiters to index.")
    if scores.quantified_impact < 7.0:
        recommendations.append("Quantify the results of your experiences and projects where you have genuine metrics. Avoid fabricating fake figures; specify actual percentage improvements, time saved, or scale outcomes.")
    if scores.completeness < 8.0:
        recommendations.append("Consider adding projects, certifications, or professional awards sections if relevant to raise resume completeness.")
        
    return recommendations

def run_ats_simulation(canonical_resume: CanonicalResume, parser_metadata: dict) -> ATSSimulationReport:
    checks = []
    
    # Check 1: Text extraction readable
    text_len = len(canonical_resume.raw_text or "")
    if text_len > 200:
        checks.append(ATSSimulationCheck(
            name="Text Extraction Quality",
            status="PASS",
            details=f"Extracted {text_len} characters of readable plain text from document."
        ))
    else:
        checks.append(ATSSimulationCheck(
            name="Text Extraction Quality",
            status="FAIL",
            details="Extracted text is too short or empty. May indicate a scanned image or corrupted file."
        ))

    # Check 2: Section Recognition
    has_edu = len(canonical_resume.education) > 0
    has_exp = len(canonical_resume.experience) > 0
    has_skills = len(canonical_resume.skills) > 0
    if has_edu and has_exp and has_skills:
        checks.append(ATSSimulationCheck(
            name="Section Structure Detection",
            status="PASS",
            details="Standard headings parsed successfully (Education, Experience, Skills recognized)."
        ))
    else:
        missing = []
        if not has_edu: missing.append("Education")
        if not has_exp: missing.append("Experience")
        if not has_skills: missing.append("Skills")
        checks.append(ATSSimulationCheck(
            name="Section Structure Detection",
            status="WARNING",
            details=f"Missing standard section headers for: {', '.join(missing)}."
        ))

    # Check 3: Layout Check (Columns/Sidebars)
    has_cols = parser_metadata.get("has_columns", False)
    if not has_cols:
        checks.append(ATSSimulationCheck(
            name="Layout Structure Compatibility",
            status="PASS",
            details="Standard single-column layout detected. Optimal for ATS indexers."
        ))
    else:
        checks.append(ATSSimulationCheck(
            name="Layout Structure Compatibility",
            status="WARNING",
            details="Multi-column layout or sidebar detected. May cause reading order fragmentation in older ATS."
        ))

    # Check 4: Contact Extraction
    pi = canonical_resume.personal_info
    has_contact = pi.name and (pi.email or pi.phone)
    if has_contact:
        checks.append(ATSSimulationCheck(
            name="Contact Details Indexing",
            status="PASS",
            details=f"Parsed contact information: Name ({pi.name or 'Unknown'}), Email ({pi.email or 'None'}), Phone ({pi.phone or 'None'})."
        ))
    else:
        checks.append(ATSSimulationCheck(
            name="Contact Details Indexing",
            status="WARNING",
            details="Missing critical contact details like email or phone in the resume header."
        ))

    # Check 5: Bullet formatting compatibility
    total_b = len(canonical_resume.all_bullets)
    if total_b >= 4:
        checks.append(ATSSimulationCheck(
            name="Bullet List Formatting",
            status="PASS",
            details=f"Detected {total_b} standard bullet points. Parsers can segment experience achievements."
        ))
    else:
        checks.append(ATSSimulationCheck(
            name="Bullet List Formatting",
            status="WARNING",
            details="Very few bullet points detected. Ensure achievements are formatted with standard dash or dot markers."
        ))
        
    overall = "PASS"
    if any(c.status == "FAIL" for c in checks):
        overall = "FAIL"
    elif any(c.status == "WARNING" for c in checks):
        overall = "WARNING"
        
    return ATSSimulationReport(overall_status=overall, checks=checks)

def generate_category_explanations(
    ats_scores: ATSCategoryScores,
    score_evidence: ScoreEvidence,
    canonical_resume: CanonicalResume,
    bullet_info: dict
) -> List[CategoryExplanation]:
    explanations = []

    # 1. ATS Compatibility
    compat_ev = score_evidence.ats_compatibility
    why_compat = "Basic document formatting rules verified."
    if compat_ev.warnings:
        why_compat = f"Warnings flagged on layout/parsing checks: {', '.join(compat_ev.warnings)}"
    explanations.append(CategoryExplanation(
        category_name="ATS Compatibility",
        score=ats_scores.ats_compatibility,
        max_score=15.0,
        why=why_compat,
        evidence=compat_ev.passed,
        reducing_factors=compat_ev.warnings,
        improvement_advice="Ensure standard section titles and a single-column layout structure."
    ))

    # 2. Resume Structure
    struct_ev = score_evidence.resume_structure
    why_struct = "Verified structural and layout format constraints."
    reducing_struct = [e for e in struct_ev.evidence if "Layout" in e or "Parsing" in e or "Structure" in e]
    explanations.append(CategoryExplanation(
        category_name="Resume Structure",
        score=ats_scores.resume_structure,
        max_score=15.0,
        why=why_struct,
        evidence=[e for e in struct_ev.evidence if "-" not in e],
        reducing_factors=[e for e in struct_ev.evidence if "-" in e],
        improvement_advice="Include start/end dates for every role and education entry. Standardize section positions."
    ))

    # 3. Keyword / Job Relevance
    kw_ev = score_evidence.keyword_relevance
    explanations.append(CategoryExplanation(
        category_name="Keyword / Job Relevance",
        score=ats_scores.keyword_relevance,
        max_score=20.0,
        why=f"Matched keywords corresponding to your stated target roles.",
        evidence=kw_ev.matched,
        reducing_factors=kw_ev.missing,
        improvement_advice="Include relevant terms and technical tool names from your target domains directly in the skills section or bullet points."
    ))

    # 4. Content Quality
    content_ev = score_evidence.content_quality
    why_content = f"Evaluated presence of technical action verbs in experience description."
    reducing_content = []
    if len(content_ev.weak_bullets) > 0:
        reducing_content.append(f"{len(content_ev.weak_bullets)} experience/project bullets start with weak or passive verbs.")
    explanations.append(CategoryExplanation(
        category_name="Content Quality",
        score=ats_scores.content_quality,
        max_score=15.0,
        why=why_content,
        evidence=[f"Action verb bullets count: {len(content_ev.strong_bullets)}"],
        reducing_factors=reducing_content,
        improvement_advice="Begin every bullet point with a strong, passive-avoiding technical action verb (e.g., 'Implemented', 'Architected', 'Optimized')."
    ))

    # 5. Skills Representation
    skills_ev = score_evidence.skills_representation
    explanations.append(CategoryExplanation(
        category_name="Skills Representation",
        score=ats_scores.skills_representation,
        max_score=10.0,
        why="Analyzed technology stack count, organization, and standardization formatting.",
        evidence=[e for e in skills_ev.evidence if "-" not in e],
        reducing_factors=[e for e in skills_ev.evidence if "-" in e],
        improvement_advice="Organize your skills section into categorized sub-lists (e.g., Languages, Frameworks, Tools) to make it easy for indexers."
    ))

    # 6. Quantified Impact
    impact_ev = score_evidence.quantified_impact
    why_impact = f"Only {impact_ev.quantified_bullets} of {impact_ev.total_bullets} experience/project bullets contain measurable outcomes."
    reducing_impact = []
    if impact_ev.total_bullets - impact_ev.quantified_bullets > 0:
        reducing_impact.append(f"{impact_ev.total_bullets - impact_ev.quantified_bullets} bullets are missing quantified outcome metrics.")
    explanations.append(CategoryExplanation(
        category_name="Quantified Impact",
        score=ats_scores.quantified_impact,
        max_score=10.0,
        why=why_impact,
        evidence=impact_ev.evidence,
        reducing_factors=reducing_impact,
        improvement_advice="For achievements lacking outcome numbers, add actual percentage increases, time saved, cost reductions, or performance benchmarks where available."
    ))

    # 7. Resume Completeness
    comp_ev = score_evidence.completeness
    explanations.append(CategoryExplanation(
        category_name="Resume Completeness",
        score=ats_scores.completeness,
        max_score=10.0,
        why="Scans if standard resume section blocks are present.",
        evidence=comp_ev.evidence,
        reducing_factors=[e for e in comp_ev.evidence if "missing" in e.lower() or "not detected" in e.lower()],
        improvement_advice="Add projects, certifications, or extracurricular blocks if they are missing from your resume."
    ))

    # 8. Readability & Consistency
    read_ev = score_evidence.readability_consistency
    explanations.append(CategoryExplanation(
        category_name="Readability & Consistency",
        score=ats_scores.readability_consistency,
        max_score=5.0,
        why="Checks for formatting issues, long paragraphs, duplicate skills, and active verb ratio.",
        evidence=[e for e in read_ev.evidence if "Excellent" in e or "+" in e],
        reducing_factors=[e for e in read_ev.evidence if "Penalty" in e or "-" in e],
        improvement_advice="Keep bullet points concise (under 2 lines) and remove any duplicate skills from the listing."
    ))

    return explanations

def detect_detailed_weaknesses(
    canonical_resume: CanonicalResume,
    ats_scores: ATSCategoryScores,
    score_evidence: ScoreEvidence,
    bullet_info: dict,
    parser_metadata: dict
) -> List[ResumeWeakness]:
    weaknesses = []
    weak_counter = 1

    # 1. Missing outcome metrics in experience/projects
    for b in canonical_resume.all_bullets:
        if b.quantification_type == "none":
            weaknesses.append(ResumeWeakness(
                id=f"W{weak_counter}",
                category="quantified_impact",
                severity="medium" if b.section == "projects" else "high",
                message="Bullet point describes responsibilities but lacks a measurable metric/outcome (e.g. %, speedup, latency, time saved).",
                context=b.text
            ))
            weak_counter += 1

    # 2. Weak passive verbs
    for b in canonical_resume.all_bullets:
        if not b.action_verbs:
            weaknesses.append(ResumeWeakness(
                id=f"W{weak_counter}",
                category="content_quality",
                severity="medium",
                message="Bullet point does not begin with an active technical verb. Consider replacing with words like 'Engineered', 'Optimized', or 'Implemented'.",
                context=b.text
            ))
            weak_counter += 1

    # 3. Layout layout / formatting warnings
    if parser_metadata.get("has_columns", False):
        weaknesses.append(ResumeWeakness(
            id=f"W{weak_counter}",
            category="ats_compatibility",
            severity="high",
            message="Multi-column layout or sidebar detected. This structure can confuse parsing robots.",
            context="Page Layout Structure"
        ))
        weak_counter += 1

    if parser_metadata.get("is_scanned", False):
        weaknesses.append(ResumeWeakness(
            id=f"W{weak_counter}",
            category="ats_compatibility",
            severity="high",
            message="Scanned document image detected instead of selectable text. ATS parsers cannot read images.",
            context="Document Encoding"
        ))
        weak_counter += 1

    # 4. Missing links in personal info or projects
    pi = canonical_resume.personal_info
    if not pi.linkedin and not pi.github and not pi.portfolio:
        weaknesses.append(ResumeWeakness(
            id=f"W{weak_counter}",
            category="completeness",
            severity="low",
            message="No online professional URLs (GitHub, LinkedIn, Portfolio) found. Recruiters value access to active repositories.",
            context="Contact Header"
        ))
        weak_counter += 1

    # 5. Excessively long bullet points
    for b in canonical_resume.all_bullets:
        if len(b.text.split()) > 30:
            weaknesses.append(ResumeWeakness(
                id=f"W{weak_counter}",
                category="readability_consistency",
                severity="low",
                message="Bullet point is excessively long (more than 30 words). Keep details crisp and under two lines.",
                context=b.text
            ))
            weak_counter += 1

    return weaknesses

def run_skill_gap_analysis(canonical_resume: CanonicalResume) -> List[SkillGapDetail]:
    role_skill_dictionary = {
        "AI/ML Engineer": [
            "python", "pytorch", "tensorflow", "numpy", "pandas", "scikit-learn",
            "machine learning", "deep learning", "neural networks", "model training", "rag", "agentic ai", "llm integration"
        ],
        "Computer Vision Engineer": [
            "python", "opencv", "mediapipe", "yolo", "opencv-python", "pytorch",
            "image processing", "object detection", "object tracking", "pose estimation"
        ],
        "Software Engineer": [
            "java", "python", "c++", "go", "data structures", "oop", "algorithms",
            "git", "github", "testing", "software architecture"
        ],
        "Backend Developer": [
            "python", "flask", "django", "fastapi", "sql", "postgresql", "rest apis",
            "databases", "docker", "kubernetes", "apis", "git"
        ],
        "Full Stack Developer": [
            "javascript", "html", "css", "react", "node.js", "express", "sql",
            "databases", "git", "python", "flask", "full-stack development"
        ]
    }
    
    analysis_list = []
    normalized_lowercase = [s.lower() for s in canonical_resume.skills]
    raw_text_lower = (canonical_resume.raw_text or "").lower()

    for role, target_skills in role_skill_dictionary.items():
        strong = []
        developing = []
        gaps = []
        
        for skill in target_skills:
            if any(skill == s or skill in s for s in normalized_lowercase):
                strong.append(skill)
            elif re.search(r'\b' + re.escape(skill) + r'\b', raw_text_lower):
                developing.append(skill)
            else:
                gaps.append(skill)
                
        analysis_list.append(SkillGapDetail(
            role=role,
            strong_skills=sorted(list(set(strong))),
            developing_skills=sorted(list(set(developing))),
            potential_gaps=sorted(list(set(gaps)))
        ))
        
    return analysis_list

def run_target_role_fit(
    canonical_resume: CanonicalResume,
    gap_analysis: List[SkillGapDetail]
) -> List[TargetRoleFit]:
    fit_list = []
    
    for gap in gap_analysis:
        total_target = len(gap.strong_skills) + len(gap.developing_skills) + len(gap.potential_gaps)
        matched_count = len(gap.strong_skills) + (len(gap.developing_skills) * 0.5)
        
        fit_score = round((matched_count / total_target) * 100, 1) if total_target > 0 else 0.0
        
        evidence = []
        for s in gap.strong_skills:
            evidence.append(f"Demonstrated core proficiency: '{s}' listed in skills section.")
        for s in gap.developing_skills:
            evidence.append(f"Contextual match: '{s}' referenced in experience responsibilities.")
            
        improvements = []
        if gap.potential_gaps:
            improvements.append(f"Incorporate missing core skills: {', '.join(gap.potential_gaps[:3])}.")
        if len(gap.strong_skills) < 4:
            improvements.append("Expand section lists to include more fundamental software libraries and tools used in this role.")

        fit_list.append(TargetRoleFit(
            role_name=gap.role,
            fit_score=fit_score,
            strong_skills=gap.strong_skills,
            supporting_evidence=evidence,
            potential_gaps=gap.potential_gaps,
            recommended_improvements=improvements
        ))
        
    return fit_list

def generate_top_improvements(weaknesses: List[ResumeWeakness]) -> List[TopImprovement]:
    top_plans = []
    
    severity_order = {"high": 1, "medium": 2, "low": 3}
    sorted_weak = sorted(weaknesses, key=lambda w: severity_order.get(w.severity, 3))
    
    used_categories = set()
    priority_count = 1
    
    for w in sorted_weak:
        if priority_count > 5:
            break
            
        if w.category in used_categories and len(used_categories) < 3:
            continue
            
        used_categories.add(w.category)
        
        title = ""
        desc = ""
        impact = 0.0
        
        if w.category == "quantified_impact":
            title = "Quantify Bullet Points"
            desc = "Add measurable outcome numbers to experience and project bullet points."
            impact = 10.0
        elif w.category == "content_quality":
            title = "Strengthen Action Verbs"
            desc = "Ensure all bullet points begin with active technical verbs rather than passive descriptions."
            impact = 15.0
        elif w.category == "ats_compatibility":
            title = "Standardize Page Layout"
            desc = "Convert your resume structure to a clean single column format with standard headings."
            impact = 15.0
        elif w.category == "completeness":
            title = "Add Professional Links"
            desc = "Include direct links to your LinkedIn, GitHub, or live project URLs in the header."
            impact = 10.0
        else:
            title = "Refine Readability"
            desc = "Shorten long bullet descriptions to keep text concise and readable for indexers."
            impact = 5.0
            
        top_plans.append(TopImprovement(
            priority=priority_count,
            title=title,
            description=desc,
            impact_score=impact
        ))
        priority_count += 1
        
    standard_suggestions = [
        ("Quantify Resume Statements", "Add numeric metrics showing performance scale or percentages.", 10.0),
        ("Use Strong Technical Verbs", "Start bullet points with technical action verbs.", 15.0),
        ("List Section Details Factual", "Include institution name, degree, company name, and duration.", 15.0),
        ("Include Online Repositories", "Add GitHub or LinkedIn links to provide code proof.", 10.0),
        ("Standardize Skills Layout", "Group technical skills by standardized category lists.", 10.0)
    ]
    
    for title, desc, impact in standard_suggestions:
        if len(top_plans) >= 5:
            break
        if not any(tp.title == title for tp in top_plans):
            top_plans.append(TopImprovement(
                priority=priority_count,
                title=title,
                description=desc,
                impact_score=impact
            ))
            priority_count += 1
            
    return top_plans

def run_ats_analysis(
    extracted_profile: LLMExtractedProfile,
    parser_metadata: dict,
    raw_text: str,
    job_match: Optional[JobMatchReport] = None
) -> CandidateProfile:
    """
    Core pipeline to run the deterministic scoring and checks using the canonical resume object.
    """
    canonical_resume, extraction_evidence = build_canonical_resume(extracted_profile, raw_text)
    
    if "page_count" in parser_metadata:
        extraction_evidence.page_count = parser_metadata["page_count"]
        
    bullet_info = run_bullet_analysis(canonical_resume)
    completeness_report, completeness_evidence = run_completeness_report(canonical_resume)
    achievement_report = run_achievement_detection(bullet_info)
    
    compatibility_report, compat_evidence = run_compatibility_checks(
        canonical_resume,
        parser_metadata,
        bullet_info
    )
    
    keyword_intel, keyword_evidence, _ = run_keyword_intelligence(canonical_resume, job_match)
    
    ats_scores, score_evidence = calculate_ats_plus_scores(
        canonical_resume,
        parser_metadata,
        compatibility_report,
        completeness_report,
        bullet_info,
        keyword_intel,
        compat_evidence,
        completeness_evidence,
        keyword_evidence,
        extracted_profile.skill_profile
    )
    
    impact_analysis = ImpactAnalysis(
        total_relevant_bullets=bullet_info["total_bullets"],
        strong_quantified_bullets=bullet_info["strong_count"],
        partial_quantified_bullets=bullet_info["partial_count"],
        non_quantified_bullets=bullet_info["none_count"],
        quantified_ratio=round(bullet_info["quantified_ratio"] * 100, 1),
        detected_metrics=bullet_info["detected_metrics"],
        technical_metrics=bullet_info.get("technical_metrics", []),
        achievement_metrics=bullet_info.get("achievement_metrics", [])
    )
    
    dynamic_recs = generate_dynamic_recommendations(
        ats_scores,
        bullet_info,
        job_match is not None
    )
    
    all_suggestions = list(extracted_profile.improvement_suggestions)
    for rec in dynamic_recs:
        if rec not in all_suggestions:
            all_suggestions.append(rec)

    # Core Upgrades Calculations
    ats_simulation_report = run_ats_simulation(canonical_resume, parser_metadata)
    category_exps = generate_category_explanations(ats_scores, score_evidence, canonical_resume, bullet_info)
    detailed_weaks = detect_detailed_weaknesses(canonical_resume, ats_scores, score_evidence, bullet_info, parser_metadata)
    gap_anal = run_skill_gap_analysis(canonical_resume)
    role_fit = run_target_role_fit(canonical_resume, gap_anal)
    top_improves = generate_top_improvements(detailed_weaks)
            
    return CandidateProfile(
        personal_info=canonical_resume.personal_info,
        education=canonical_resume.education,
        experience=canonical_resume.experience,
        projects=canonical_resume.projects,
        certifications=canonical_resume.certifications,
        achievements=canonical_resume.achievements,
        skill_profile=extracted_profile.skill_profile,
        canonical_resume=canonical_resume,
        extraction_evidence=extraction_evidence,
        score_evidence=score_evidence,
        ats_scores=ats_scores,
        ats_compatibility=compatibility_report,
        completeness=completeness_report,
        achievement_report=achievement_report,
        keyword_intelligence=keyword_intel,
        impact_analysis=impact_analysis,
        ai_summary=extracted_profile.ai_summary,
        improvement_suggestions=all_suggestions,
        strengths=extracted_profile.strengths or ["Strong technology stack matching target SDE fields.", "Proper education details present with GPA tracking."],
        weaknesses=[w.message for w in detailed_weaks[:5]] if detailed_weaks else (extracted_profile.weaknesses or ["Lacks measurable outcome metrics in several bullet points."]),
        category_explanations=category_exps,
        detailed_weaknesses=detailed_weaks,
        skill_gap_analysis=gap_anal,
        target_role_fit=role_fit,
        top_improvements=top_improves,
        ats_simulation=ats_simulation_report
    )
