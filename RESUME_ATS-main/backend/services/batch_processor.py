import io
import zipfile
import logging
from typing import List, Tuple, Dict, Any, Optional

import spacy
from sentence_transformers import SentenceTransformer

from backend.services.resume_parser import parse_resume_file
from backend.services.resume_analyzer import analyze_full_resume
from backend.models.schemas import CandidateRankItem, BatchAnalysisResponse

logger = logging.getLogger('ats_resume_scorer')

ALLOWED_EXTENSIONS = ('.pdf', '.docx', '.doc', '.txt')


def extract_files_from_zip(zip_bytes: bytes) -> List[Tuple[str, bytes]]:
    """Extract all valid resume files from a zip archive."""
    extracted_files = []
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for file_info in zf.infolist():
                if file_info.is_dir():
                    continue
                filename = file_info.filename
                if filename.startswith('__MACOSX') or filename.startswith('.') or '/.' in filename:
                    continue
                basename = filename.split('/')[-1]
                if any(basename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
                    file_bytes = zf.read(file_info.filename)
                    if len(file_bytes) > 0:
                        extracted_files.append((basename, file_bytes))
    except Exception as exc:
        logger.error(f"Failed to extract zip file: {exc}")

    return extracted_files


def process_resume_batch(
    file_list: List[Tuple[str, bytes]],
    job_description: str,
    nlp: spacy.Language,
    embedder: SentenceTransformer,
) -> BatchAnalysisResponse:
    """
    Processes a list of (filename, file_bytes) against a job description.
    Ranks candidates by match percentage / ATS score and categorizes status.
    """
    raw_results = []
    total_score_sum = 0.0

    for filename, file_bytes in file_list:
        try:
            resume_text, _metadata = parse_resume_file(file_bytes, filename)
            if not resume_text or len(resume_text.strip()) < 20:
                logger.warning(f"File '{filename}' yielded insufficient text.")
                continue

            analysis = analyze_full_resume(
                resume_text=resume_text,
                nlp=nlp,
                embedder=embedder,
                job_description=job_description if job_description.strip() else None
            )

            ats_score = float(analysis.get('ATS_score', analysis.get('ats_score', 0.0)))

            jd_comp = analysis.get('jd_comparison') or analysis.get('jd_match_analysis')
            if jd_comp and isinstance(jd_comp, dict):
                match_pct = float(jd_comp.get('match_percentage', ats_score))
                matched_skills = jd_comp.get('matched_keywords', [])
                missing_skills = jd_comp.get('missing_keywords', [])
            elif hasattr(jd_comp, 'match_percentage'):
                match_pct = float(jd_comp.match_percentage)
                matched_skills = jd_comp.matched_keywords
                missing_skills = jd_comp.missing_keywords
            else:
                match_pct = ats_score
                matched_skills = analysis.get('matched_keywords', analysis.get('skills', []))[:10]
                missing_skills = analysis.get('missing_keywords', [])[:10]

            candidate_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
            if len(candidate_name) > 40:
                candidate_name = candidate_name[:37] + "..."

            email = None
            phone = None

            raw_results.append({
                'filename': filename,
                'candidate_name': candidate_name,
                'email': email,
                'phone': phone,
                'ats_score': round(ats_score, 1),
                'jd_match_pct': round(match_pct, 1),
                'matched_skills': list(matched_skills[:10]),
                'missing_skills': list(missing_skills[:10]),
                'strengths': analysis.get('strengths', [])[:3],
                'full_analysis': analysis,
            })
            total_score_sum += match_pct

        except Exception as exc:
            logger.error(f"Error processing candidate file '{filename}': {exc}")
            continue

    raw_results.sort(key=lambda x: x['jd_match_pct'], reverse=True)

    candidates: List[CandidateRankItem] = []
    shortlisted_count = 0
    under_review_count = 0
    not_suitable_count = 0

    for idx, item in enumerate(raw_results, start=1):
        match_score = item['jd_match_pct']
        if match_score >= 75.0:
            status = "Shortlisted"
            shortlisted_count += 1
        elif match_score >= 55.0:
            status = "Under Review"
            under_review_count += 1
        else:
            status = "Not Suitable"
            not_suitable_count += 1

        candidates.append(CandidateRankItem(
            rank=idx,
            filename=item['filename'],
            candidate_name=item['candidate_name'],
            email=item['email'],
            phone=item['phone'],
            ats_score=item['ats_score'],
            jd_match_pct=item['jd_match_pct'],
            status=status,
            matched_skills=item['matched_skills'],
            missing_skills=item['missing_skills'],
            top_strengths=item['strengths'],
            full_analysis=item['full_analysis'],
        ))

    total = len(candidates)
    avg_score = round(total_score_sum / total, 1) if total > 0 else 0.0
    top_score = candidates[0].jd_match_pct if total > 0 else 0.0

    return BatchAnalysisResponse(
        job_title="Target Job Position",
        total_candidates=total,
        shortlisted_count=shortlisted_count,
        under_review_count=under_review_count,
        not_suitable_count=not_suitable_count,
        top_score=top_score,
        average_score=avg_score,
        candidates=candidates
    )
