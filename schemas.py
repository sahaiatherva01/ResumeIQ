from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class PersonalInfo(BaseModel):
    name: Optional[str] = Field(default=None, description="Full name of the candidate")
    email: Optional[str] = Field(default=None, description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: Optional[str] = Field(default=None, description="Current location (City, State/Country)")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    github: Optional[str] = Field(default=None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(default=None, description="Portfolio or personal website URL")

class Education(BaseModel):
    institution: Optional[str] = Field(default=None, description="Name of the school/university")
    degree: Optional[str] = Field(default=None, description="Degree earned (e.g., B.S., M.S.)")
    field: Optional[str] = Field(default=None, description="Field of study or major")
    gpa: Optional[str] = Field(default=None, description="GPA if mentioned (e.g., 3.8/4.0)")
    start_year: Optional[str] = Field(default=None, description="Start year or date")
    graduation_year: Optional[str] = Field(default=None, description="Graduation year or date")

class Experience(BaseModel):
    company: Optional[str] = Field(default=None, description="Name of the company or organization")
    role: Optional[str] = Field(default=None, description="Job title")
    duration: Optional[str] = Field(default=None, description="Employment duration (dates or length)")
    responsibilities: List[str] = Field(default_factory=list, description="Responsibilities and descriptions of tasks")
    technologies: List[str] = Field(default_factory=list, description="Technologies, programming languages, or tools used in this role")
    achievements: List[str] = Field(default_factory=list, description="Key achievements in this role")

class Project(BaseModel):
    name: Optional[str] = Field(default=None, description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    technologies: List[str] = Field(default_factory=list, description="Technologies and tools used")
    domain: Optional[str] = Field(default=None, description="Project domain (e.g., Frontend, Backend, Machine Learning)")
    achievements: Optional[str] = Field(default=None, description="Key achievements or outcomes of the project")
    links: List[str] = Field(default_factory=list, description="URLs linked to the project")

class Certification(BaseModel):
    name: Optional[str] = Field(default=None, description="Name of the certification")
    issuer: Optional[str] = Field(default=None, description="Issuing organization")
    date: Optional[str] = Field(default=None, description="Date issued or expiration")

class Achievement(BaseModel):
    description: Optional[str] = Field(default=None, description="Description of the achievement")
    category: Optional[str] = Field(default=None, description="Category (award/publication/leadership/ranking)")

class SkillProfile(BaseModel):
    raw_skills: List[str] = Field(default_factory=list, description="Raw list of skills extracted directly from the resume")
    categorized_skills: Dict[str, List[str]] = Field(default_factory=dict, description="Dictionary mapping categories (e.g., Languages, Frameworks, Tools) to lists of skills")
    normalized_skills: List[str] = Field(default_factory=list, description="Normalized, canonical, and deduplicated skills list")

class ATSCategoryScores(BaseModel):
    ats_compatibility: float = Field(..., description="ATS Compatibility score (out of 15)")
    resume_structure: float = Field(..., description="Resume Structure score (out of 15)")
    keyword_relevance: float = Field(..., description="Keyword / Job Relevance score (out of 20)")
    content_quality: float = Field(..., description="Content Quality score (out of 15)")
    skills_representation: float = Field(..., description="Skills Representation score (out of 10)")
    quantified_impact: float = Field(..., description="Quantified Impact score (out of 10)")
    completeness: float = Field(..., description="Completeness score (out of 10)")
    readability_consistency: float = Field(..., description="Readability & Consistency score (out of 5)")
    overall_score: float = Field(..., description="Overall score out of 100")

class CompatibilityCheck(BaseModel):
    name: str = Field(..., description="Name of the compatibility check")
    status: str = Field(..., description="Status (pass/warn/fail)")
    message: str = Field(..., description="Explanation of the status")

class ATSCompatibilityReport(BaseModel):
    checks: List[CompatibilityCheck] = Field(default_factory=list, description="List of formatting and parsing checks")

class CompletenessReport(BaseModel):
    sections: Dict[str, bool] = Field(..., description="Dictionary mapping section names to detected boolean")
    completeness_percent: float = Field(..., description="Completeness percentage (0-100)")

class AchievementReport(BaseModel):
    count: int = Field(..., description="Number of detected quantified achievements")
    detected_achievements: List[str] = Field(default_factory=list, description="List of detected quantified achievements text")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions for bullet points lacking metrics")

class JobMatchReport(BaseModel):
    matched_keywords: List[str] = Field(default_factory=list, description="Matched keywords from JD")
    missing_keywords: List[str] = Field(default_factory=list, description="Missing keywords from JD")
    matched_required_skills: List[str] = Field(default_factory=list, description="Matched required skills from JD")
    missing_required_skills: List[str] = Field(default_factory=list, description="Missing required skills from JD")
    matched_preferred_skills: List[str] = Field(default_factory=list, description="Matched preferred skills from JD")
    missing_preferred_skills: List[str] = Field(default_factory=list, description="Missing preferred skills from JD")
    jd_match_score: float = Field(..., description="Match percentage score from 0 to 100")

class KeywordIntelligence(BaseModel):
    domain_strength: Dict[str, str] = Field(..., description="Dictionary of domain category -> relative strength (High/Medium/Low)")
    job_match: Optional[JobMatchReport] = Field(default=None, description="Optional JD match details")
    is_jd_provided: bool = Field(default=False, description="Whether a Job Description was provided")
    label: str = Field(default="General Keyword Relevance", description="UI label for this keyword section")

class ImpactAnalysis(BaseModel):
    total_relevant_bullets: int = Field(..., description="Total bullet points extracted from experience and projects")
    strong_quantified_bullets: int = Field(..., description="Count of bullets with strong metrics")
    partial_quantified_bullets: int = Field(..., description="Count of bullets with partial numeric context")
    non_quantified_bullets: int = Field(..., description="Count of bullets with no metrics")
    quantified_ratio: float = Field(..., description="Percentage of bullets with strong metrics")
    detected_metrics: List[str] = Field(default_factory=list, description="Extracted metric text phrases")
    technical_metrics: List[str] = Field(default_factory=list, description="Numeric measurements representing implementation detail")
    achievement_metrics: List[str] = Field(default_factory=list, description="Percentages, time saved, cost reductions, throughput")

# --- Canonical Evidence Models ---

class CanonicalBullet(BaseModel):
    id: str = Field(..., description="Unique ID for this bullet point")
    section: str = Field(..., description="The main section this bullet point came from (e.g. experience, projects)")
    subsection: Optional[str] = Field(default=None, description="Detailed section name")
    entity: Optional[str] = Field(default=None, description="The company name or project name")
    role: Optional[str] = Field(default=None, description="The job title or role name")
    text: str = Field(..., description="The verbatim text of the bullet point")
    metrics: List[str] = Field(default_factory=list, description="List of all numbers/metrics found in this bullet")
    has_metric: bool = Field(default=False, description="True if the bullet contains any metrics")
    skills: List[str] = Field(default_factory=list, description="List of skills referenced in this bullet")
    action_verbs: List[str] = Field(default_factory=list, description="List of technical action verbs present")
    quantification_type: str = Field(..., description="Classification: strong, partial, or none")

class CanonicalResume(BaseModel):
    personal_info: PersonalInfo
    summary: Optional[str] = Field(default=None, description="verbatim summary or objective text")
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    research_experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list, description="Normalized flat list of skills")
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    extracurriculars: List[Experience] = Field(default_factory=list)
    all_bullets: List[CanonicalBullet] = Field(default_factory=list)
    raw_text: str = Field(..., description="verbatim raw text extracted from file")

class ItemEvidence(BaseModel):
    item_type: str = Field(..., description="E.g., experience, education, certification")
    field_name: str = Field(..., description="E.g., company, role, institution, degree")
    extracted_value: str = Field(..., description="The value extracted by LLM")
    source: str = Field(default="resume_text", description="The source of the evidence")
    confidence: float = Field(default=1.0, description="Confidence score from 0.0 to 1.0")
    matched_substring: Optional[str] = Field(default=None, description="The matched substring in raw text")

class ExtractionEvidence(BaseModel):
    raw_text_length: int = Field(..., description="Length of raw text")
    page_count: int = Field(..., description="Number of pages parsed")
    sections_detected: List[str] = Field(default_factory=list, description="Detected sections from raw text")
    source_bullets: List[str] = Field(default_factory=list, description="Extracted raw experience/project bullets")
    extraction_warnings: List[str] = Field(default_factory=list, description="Warnings of mismatched or hallucinated items")
    item_evidence: List[ItemEvidence] = Field(default_factory=list, description="Verification details for each property")

# --- Category Score Evidence Models ---

class ATSCompatibilityEvidence(BaseModel):
    score: float
    max_score: float = 15.0
    passed: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ResumeStructureEvidence(BaseModel):
    score: float
    max_score: float = 15.0
    evidence: List[str] = Field(default_factory=list)

class KeywordRelevanceEvidence(BaseModel):
    score: float
    max_score: float = 20.0
    matched: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)

class ContentQualityEvidence(BaseModel):
    score: float
    max_score: float = 15.0
    strong_bullets: List[str] = Field(default_factory=list)
    weak_bullets: List[str] = Field(default_factory=list)

class SkillsRepresentationEvidence(BaseModel):
    score: float
    max_score: float = 10.0
    evidence: List[str] = Field(default_factory=list)

class QuantifiedImpactEvidence(BaseModel):
    score: float
    max_score: float = 10.0
    total_bullets: int
    quantified_bullets: int
    metrics: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)

class CompletenessEvidence(BaseModel):
    score: float
    max_score: float = 10.0
    evidence: List[str] = Field(default_factory=list)

class ReadabilityConsistencyEvidence(BaseModel):
    score: float
    max_score: float = 5.0
    evidence: List[str] = Field(default_factory=list)

class ScoreEvidence(BaseModel):
    ats_compatibility: ATSCompatibilityEvidence
    resume_structure: ResumeStructureEvidence
    keyword_relevance: KeywordRelevanceEvidence
    content_quality: ContentQualityEvidence
    skills_representation: SkillsRepresentationEvidence
    quantified_impact: QuantifiedImpactEvidence
    completeness: CompletenessEvidence
    readability_consistency: ReadabilityConsistencyEvidence

class CategoryExplanation(BaseModel):
    category_name: str
    score: float
    max_score: float
    why: str
    evidence: List[str]
    reducing_factors: List[str]
    improvement_advice: str

class ResumeWeakness(BaseModel):
    id: str
    category: str
    severity: str  # "high", "medium", "low"
    message: str
    context: Optional[str] = None

class SkillGapDetail(BaseModel):
    role: str
    strong_skills: List[str]
    developing_skills: List[str]
    potential_gaps: List[str]

class TargetRoleFit(BaseModel):
    role_name: str
    fit_score: float
    strong_skills: List[str]
    supporting_evidence: List[str]
    potential_gaps: List[str]
    recommended_improvements: List[str]

class TopImprovement(BaseModel):
    priority: int
    title: str
    description: str
    impact_score: float

class ATSSimulationCheck(BaseModel):
    name: str
    status: str  # PASS, WARNING, FAIL
    details: str

class ATSSimulationReport(BaseModel):
    overall_status: str  # PASS, WARNING, FAIL
    checks: List[ATSSimulationCheck]

class CandidateProfile(BaseModel):
    personal_info: PersonalInfo
    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    skill_profile: SkillProfile
    canonical_resume: CanonicalResume
    extraction_evidence: ExtractionEvidence
    score_evidence: ScoreEvidence
    ats_scores: ATSCategoryScores
    ats_compatibility: ATSCompatibilityReport
    completeness: CompletenessReport
    achievement_report: AchievementReport
    keyword_intelligence: KeywordIntelligence
    impact_analysis: ImpactAnalysis
    ai_summary: str = Field(..., description="AI-generated recruiter-style summary")
    improvement_suggestions: List[str] = Field(default_factory=list, description="AI-generated improvement suggestions")
    strengths: List[str] = Field(default_factory=list, description="Strengths detected in the resume")
    weaknesses: List[str] = Field(default_factory=list, description="Weaknesses detected in the resume")
    category_explanations: List[CategoryExplanation] = Field(default_factory=list, description="Explanations for each ATS category score")
    detailed_weaknesses: List[ResumeWeakness] = Field(default_factory=list, description="Detailed list of specific weaknesses in the resume")
    skill_gap_analysis: List[SkillGapDetail] = Field(default_factory=list, description="Domain and role specific skill gaps")
    target_role_fit: List[TargetRoleFit] = Field(default_factory=list, description="Target role alignment score and feedback")
    top_improvements: List[TopImprovement] = Field(default_factory=list, description="Top 5 prioritized changes to make")
    ats_simulation: Optional[ATSSimulationReport] = Field(default=None, description="ATS parsing simulation results")
    version_id: Optional[str] = Field(default=None, description="The unique timestamp ID of this analysis version")

