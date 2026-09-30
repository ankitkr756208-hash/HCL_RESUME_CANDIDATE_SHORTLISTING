from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ComponentScores(BaseModel):
    formatting: float
    keywords: float
    content: float
    skill_validation: float
    ats_compatibility: float

class JDComparison(BaseModel):
    match_percentage: float
    semantic_similarity: float
    matched_keywords: List[str]
    missing_keywords: List[str]
    skills_gap: List[str]

class SkillValidationDetails(BaseModel):
    validated: List[Dict[str, Any]] = []       # [{'skill': str, 'projects': [str]}]
    unvalidated: List[str] = []                # ['Flask', 'A/B Testing', ...]
    total: int = 0
    validated_count: int = 0
    validation_pct: float = 0.0

class IssueDetail(BaseModel):
    issue_title: str
    severity_level: str
    ats_impact: str
    explanation: str
    where_it_appears: str
    how_to_fix: str
    action_items: List[str] = []
    example_improvement: str

class AnalysisResponse(BaseModel):
    ATS_score: float
    component_scores: ComponentScores
    issues_summary: List[str]
    detailed_feedback: List[IssueDetail]
    jd_match_analysis: Optional[JDComparison] = None
    skill_validation_details: Optional[SkillValidationDetails] = None

    ats_score: float
    keyword_match: float = 0.0
    missing_keywords: List[str] = []
    matched_keywords: List[str] = []
    suggestions: List[str] = []
    strengths: List[str] = []
    critical_issues: List[str] = []
    skills: List[str] = []
    jd_comparison: Optional[JDComparison] = None
class CandidateRankItem(BaseModel):
    rank: int
    filename: str
    candidate_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    ats_score: float
    jd_match_pct: float
    status: str  # Shortlisted, Under Review, Not Suitable
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    top_strengths: List[str] = []
    full_analysis: Optional[Dict[str, Any]] = None

class BatchAnalysisResponse(BaseModel):
    job_title: str = "Target Position"
    total_candidates: int
    shortlisted_count: int
    under_review_count: int
    not_suitable_count: int
    top_score: float
    average_score: float
    candidates: List[CandidateRankItem]

