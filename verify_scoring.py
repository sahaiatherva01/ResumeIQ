import sys
import os

from resume_parser import detect_sections
from extractor import get_mock_profile, get_mock_job_match, LLMExtractedProfile
from schemas import PersonalInfo, Education, Experience, Project, Certification, Achievement, SkillProfile, JobMatchReport
from ats_analyzer import (
    run_bullet_analysis, run_completeness_report, run_compatibility_checks,
    run_keyword_intelligence, calculate_ats_plus_scores, run_ats_analysis,
    classify_bullet_metrics, build_canonical_resume
)

# Dummy raw text matching Mercer profile perfectly
MERCER_RAW_TEXT = (
    "Alex Mercer\n"
    "alex.mercer@example.com | +1 (555) 019-2834 | San Francisco, CA\n"
    "linkedin.com/in/alex-mercer | github.com/alex-mercer | alexmercer.dev\n\n"
    "EDUCATION\n"
    "University of California, Berkeley - B.S. in Computer Science (GPA: 3.82/4.0) - 2018 to 2022\n\n"
    "EXPERIENCE\n"
    "TechCorp Solutions - Software Engineer II - June 2022 to Present\n"
    "- Developed and maintained scalable microservices using Python and Flask.\n"
    "- Improved system response latency and optimized database queries.\n"
    "- Collaborated with frontend teams to implement premium designs and responsive user experiences.\n"
    "- Mentored junior developers and participated in architectural review meetings.\n"
    "- Reduced page load time by 35% through API query optimizations.\n"
    "- Spearheaded migration of legacy services, resulting in a 20% cloud hosting cost reduction.\n\n"
    "Innovate AI - Software Engineering Intern - June 2021 to September 2021\n"
    "- Built machine learning prototypes for document scanning and text extraction.\n"
    "- Implemented responsive dashboards for monitoring backend task pipelines.\n"
    "- Wrote unit tests and automated integration testing scripts.\n"
    "- Successfully prototype achieved 92% classification accuracy.\n"
    "- Automated daily reporting pipelines, saving the operations team 5 hours per week.\n\n"
    "PROJECTS\n"
    "ResumeLens AI - An intelligent resume analyzer utilizing Gemini LLM.\n"
    "- Designed and built a complete single-page interactive report and scoring tool.\n\n"
    "CERTIFICATIONS\n"
    "AWS Certified Developer - Associate - 2023\n\n"
    "ACHIEVEMENTS\n"
    "- Dean's Honors List (UC Berkeley) - 4 semesters\n"
    "- First Place Winner - CalHacks Hackathon 2021\n"
    "Skills: Python, Flask, Docker, AWS, PostgreSQL, Git, FastAPI, React, JavaScript, HTML, CSS, PyTorch, REST APIs."
)

def run_tests():
    print("=== STARTING EVIDENCE-BASED REFINE TEST SUITE ===")

    # 1. Test metric classification rules
    print("\n[1] Testing Metric Classification Heuristics...")
    assert classify_bullet_metrics("Reduced page load time by 35%") == "strong"
    assert classify_bullet_metrics("Automated reporting pipelines saving 5 hours per week.") == "strong"
    assert classify_bullet_metrics("Managed a budget of $50K") == "strong"
    assert classify_bullet_metrics("Built 12 REST API endpoints") == "partial"
    assert classify_bullet_metrics("Developed microservices using Flask") == "none"
    print("Metric classification heuristics verified successfully.")

    # 2. Trace Alex Mercer Profile Bullet Analysis
    print("\n[2] Testing Mercer Profile Bullet Extraction...")
    mock_extracted = get_mock_profile()
    canonical_resume, ext_evidence = build_canonical_resume(mock_extracted, MERCER_RAW_TEXT)
    
    bullet_info = run_bullet_analysis(canonical_resume)
    assert bullet_info['total_bullets'] == 12, f"Expected 12 bullets, got {bullet_info['total_bullets']}"
    assert bullet_info['strong_count'] == 4, f"Expected 4 strong metrics, got {bullet_info['strong_count']}"
    assert "35%" in bullet_info['detected_metrics']
    assert "20%" in bullet_info['detected_metrics']
    assert "92%" in bullet_info['detected_metrics']
    assert any("5 hours" in m for m in bullet_info['detected_metrics'])
    print("Alex Mercer bullet parser parsed all 12 bullets and detected 4 genuine metrics successfully.")

    # 3. Test 100-Point Scoring Calculations and Sum Checks
    print("\n[3] Testing Rubric Score Calculations...")
    parser_metadata = {
        "has_columns": False,
        "is_scanned": False,
        "page_count": 1,
        "has_tables": False
    }
    
    # Case A: Resume Only (Mode A)
    print(" - Mode A: Resume Only (General Keyword Relevance)")
    profile_only = run_ats_analysis(mock_extracted, parser_metadata, MERCER_RAW_TEXT, job_match=None)
    scores_only = profile_only.ats_scores
    print(f"   * Overall Score: {scores_only.overall_score}/100")
    print(f"   * Keyword Relevance: {scores_only.keyword_relevance}/20")
    assert scores_only.keyword_relevance == 8.3, f"Expected Mode A general keyword score, got {scores_only.keyword_relevance}"
    
    # Mathematical sum check
    sum_only = (
        scores_only.ats_compatibility + scores_only.resume_structure + scores_only.keyword_relevance +
        scores_only.content_quality + scores_only.skills_representation + scores_only.quantified_impact +
        scores_only.completeness + scores_only.readability_consistency
    )
    assert round(sum_only, 1) == round(scores_only.overall_score, 1), f"Overall score does not equal category sum! Sum: {sum_only}, Overall: {scores_only.overall_score}"

    # Case B: Resume + JD (Mode B)
    print(" - Mode B: Resume + Job Description (Job-Specific ATS Match)")
    mock_jd_match = get_mock_job_match() # JD match score = 78.5
    profile_jd = run_ats_analysis(mock_extracted, parser_metadata, MERCER_RAW_TEXT, job_match=mock_jd_match)
    scores_jd = profile_jd.ats_scores
    print(f"   * Overall Score: {scores_jd.overall_score}/100")
    print(f"   * Keyword Relevance: {scores_jd.keyword_relevance}/20")
    # Expected keyword match score out of 20 = 57.5 / 100 * 20 = 11.5
    assert scores_jd.keyword_relevance == 11.5, f"Expected 11.5, got {scores_jd.keyword_relevance}"
    
    sum_jd = (
        scores_jd.ats_compatibility + scores_jd.resume_structure + scores_jd.keyword_relevance +
        scores_jd.content_quality + scores_jd.skills_representation + scores_jd.quantified_impact +
        scores_jd.completeness + scores_jd.readability_consistency
    )
    assert round(sum_jd, 1) == round(scores_jd.overall_score, 1), f"JD match overall score does not equal category sum! Sum: {sum_jd}, Overall: {scores_jd.overall_score}"
    print("Rubric scores sum checks passed.")

    # 4. Multi-Scenario Regression Tests (Scenarios 1-9)
    print("\n[4] Running 9 Scenario Regression Tests...")
    
    def create_dummy_profile(experience_bullets=None, skills=None, projects=None):
        exp_list = []
        if experience_bullets:
            exp_list = [
                Experience(
                    company="Dummy Corp",
                    role="Software Developer",
                    duration="2021-2023",
                    responsibilities=experience_bullets
                )
            ]
        proj_list = []
        if projects:
            proj_list = [
                Project(
                    name=p_name,
                    description=p_desc
                ) for p_name, p_desc in projects
            ]
        return LLMExtractedProfile(
            personal_info=PersonalInfo(name="Dummy User", email="dummy@test.com", phone="123-456-7890"),
            education=[Education(institution="Test School", degree="B.S.", field="CS")],
            experience=exp_list,
            projects=proj_list,
            certifications=[],
            achievements=[],
            skill_profile=SkillProfile(
                raw_skills=skills or ["Python"],
                normalized_skills=skills or ["Python"]
            ),
            ai_summary="Dummy candidate",
            improvement_suggestions=[],
            strengths=[],
            weaknesses=[]
        )

    meta = {"has_columns": False, "is_scanned": False, "page_count": 1}
    
    def get_dummy_raw_text(profile):
        parts = []
        parts.append(profile.personal_info.name)
        parts.append(profile.personal_info.email)
        parts.append(profile.personal_info.phone)
        for edu in profile.education:
            parts.extend([edu.institution, edu.degree, edu.field])
        for exp in profile.experience:
            parts.extend([exp.company, exp.role])
            parts.extend(exp.responsibilities)
        for proj in profile.projects:
            parts.extend([proj.name, proj.description])
        parts.extend(profile.skill_profile.normalized_skills)
        return " ".join(parts)

    # Scenario 1: Resume with no metrics
    print(" - Scenario 1: Resume with no metrics")
    prof1 = create_dummy_profile(["Wrote code in Python.", "Created database schemas."])
    prof1_res = run_ats_analysis(prof1, meta, get_dummy_raw_text(prof1))
    assert prof1_res.ats_scores.quantified_impact == 0.0
    
    # Scenario 2: Resume with 1 metric
    print(" - Scenario 2: Resume with 1 metric")
    prof2 = create_dummy_profile(["Wrote code in Python.", "Reduced response latency by 35%."])
    prof2_res = run_ats_analysis(prof2, meta, get_dummy_raw_text(prof2))
    assert prof2_res.ats_scores.quantified_impact == 5.0

    # Scenario 3: Resume with many metrics
    print(" - Scenario 3: Resume with many metrics")
    prof3 = create_dummy_profile(["Reduced costs by 20%.", "Reduced load times by 35%."])
    prof3_res = run_ats_analysis(prof3, meta, get_dummy_raw_text(prof3))
    assert prof3_res.ats_scores.quantified_impact == 10.0

    # Scenario 4: Resume with dates but no achievement metrics
    print(" - Scenario 4: Resume with dates but no achievement metrics")
    prof4 = create_dummy_profile(["Worked here from 2021 to 2023.", "Wrote backend code."])
    prof4_res = run_ats_analysis(prof4, meta, get_dummy_raw_text(prof4))
    assert prof4_res.ats_scores.quantified_impact == 0.0

    # Scenario 5: Resume with phone number but no metrics
    print(" - Scenario 5: Resume with phone number but no metrics")
    prof5 = create_dummy_profile(["Phone number is 123-456-7890.", "Developed applications."])
    prof5_res = run_ats_analysis(prof5, meta, get_dummy_raw_text(prof5))
    assert prof5_res.ats_scores.quantified_impact == 0.0

    # Scenario 6: Resume + matching JD
    print(" - Scenario 6: Resume + matching JD")
    prof6 = create_dummy_profile(skills=["Python", "Flask", "PostgreSQL"])
    jd_match_ok = JobMatchReport(
        matched_required_skills=["Python", "Flask"],
        missing_required_skills=[],
        matched_preferred_skills=["PostgreSQL"],
        missing_preferred_skills=[],
        jd_match_score=100.0
    )
    prof6_res = run_ats_analysis(prof6, meta, get_dummy_raw_text(prof6), job_match=jd_match_ok)
    assert prof6_res.ats_scores.keyword_relevance == 20.0

    # Scenario 7: Resume + unrelated JD
    print(" - Scenario 7: Resume + unrelated JD")
    prof7 = create_dummy_profile(skills=["Python"])
    jd_match_bad = JobMatchReport(
        matched_required_skills=[],
        missing_required_skills=["Java", "Spring Boot"],
        matched_preferred_skills=[],
        missing_preferred_skills=["AWS"],
        jd_match_score=0.0
    )
    prof7_res = run_ats_analysis(prof7, meta, get_dummy_raw_text(prof7), job_match=jd_match_bad)
    assert prof7_res.ats_scores.keyword_relevance == 0.0

    # Scenario 8: Resume with missing sections (completeness test)
    print(" - Scenario 8: Resume with missing sections")
    prof8 = create_dummy_profile()
    prof8_res = run_ats_analysis(prof8, meta, get_dummy_raw_text(prof8))
    assert prof8_res.completeness.completeness_percent < 80.0

    # Scenario 9: Resume with keyword stuffing penalty
    print(" - Scenario 9: Resume with keyword stuffing")
    stuffed_skills = [f"Skill{i}" for i in range(35)]
    prof9 = create_dummy_profile(skills=stuffed_skills)
    prof9_res = run_ats_analysis(prof9, meta, get_dummy_raw_text(prof9))
    assert prof9_res.ats_scores.skills_representation < 8.0

    print("All 9 scenario regression tests ran and assertions verified successfully.")
    print("\n=== ALL EVIDENCE-BASED REFINE TESTS PASSED ===")

if __name__ == "__main__":
    run_tests()
