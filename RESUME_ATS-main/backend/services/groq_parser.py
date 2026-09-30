import os
import json 
import logging
from typing import Dict

from groq import Groq

logger=logging.getLogger('ats_resume_scorer')


GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

_client = None

def _get_client() -> Groq | None:
    global _client
    if _client is None:
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            logger.warning("GROQ_API_KEY environment variable not set — using heuristic fallback parser.")
            return None
        _client = Groq(api_key=api_key)
    return _client

RESUME_SYSTEM_PROMPT = (
    "You are a resume parser. Extract information from the resume "
    "and return ONLY a valid JSON object. No explanation, no markdown."
)

RESUME_USER_PROMPT = """Extract the following from this resume and return as JSON:
{{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "linkedin": "LinkedIn URL if present, otherwise null",
  "github": "GitHub URL if present, otherwise null",
  "professional_summary": "the full text of the Summary, Profile, About Me, Objective, or Professional Summary section at the top of the resume. Copy the ENTIRE paragraph exactly as written. If no such section exists, return an empty string.",
  "skills": ["list", "of", "skills"],
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "duration_months": 0,
      "description": ""
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "year": ""
    }}
  ],
  "certifications": ["list of certifications"],
  "projects": [
    {{
      "title": "project name",
      "description": "what the project does and how it was built",
      "technologies": ["tech", "used"]
    }}
  ],
  "action_verbs": ["strong action verbs used in bullet points, e.g. developed, implemented, designed"],
  "keywords": ["important keywords and phrases from the resume for ATS matching"]
}}

Important instructions:
- For duration_months, calculate the number of months between start_date and end_date. If end_date is "Present" or "Current", calculate from start_date to now.
- For skills, extract ALL technical and soft skills mentioned anywhere in the resume.
- For action_verbs, find verbs that start bullet points or describe achievements.
- For keywords, extract noun phrases and technical terms relevant to ATS matching.
- Return ONLY valid JSON. No markdown code fences, no explanation.

Resume Text:
{raw_text}"""

def _call_groq(client: Groq, system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        temperature=0.0,
        max_tokens=4096
    )
    return response.choices[0].message.content.strip()

def _try_parse_json(text: str) -> dict | None:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.index("\n") if "\n" in cleaned else len(cleaned)
        cleaned = cleaned[first_newline + 1:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None

def parse_resume(raw_text: str) -> Dict:
    client = _get_client()
    if not client:
        return _heuristic_resume_parse(raw_text)

    try:
        prompt = RESUME_USER_PROMPT.format(raw_text=raw_text[:8000])
        raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, prompt)
        result = _try_parse_json(raw_response)

        if result is not None:
            return _validate_resume_result(result)

        logger.warning("Groq resume parse: first attempt returned invalid JSON, retrying...")
        strict_prompt = (
            "Your previous response was not valid JSON. "
            "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
            + prompt
        )
        raw_response = _call_groq(client, RESUME_SYSTEM_PROMPT, strict_prompt)
        result = _try_parse_json(raw_response)
        if result is not None:
            return _validate_resume_result(result)
    except Exception as exc:
        logger.error(f"Groq resume parsing failed: {exc}. Falling back to heuristic parser.")

    return _heuristic_resume_parse(raw_text)
    
JD_SYSTEM_PROMPT = (
    "You are a job description parser. Extract information and "
    "return ONLY a valid JSON object. No explanation, no markdown."
)

JD_USER_PROMPT = """Extract the following from this job description and return as JSON:
{{
  "job_title": "",
  "required_skills": ["list of must-have skills"],
  "preferred_skills": ["list of nice-to-have skills"],
  "experience_required": "",
  "education_required": "",
  "key_responsibilities": ["list of responsibilities"],
  "keywords": ["important keywords and phrases for ATS matching"]
}}

Important instructions:
- required_skills: skills explicitly stated as required or must-have.
- preferred_skills: skills stated as preferred, nice-to-have, or bonus.
- keywords: extract ALL important terms an ATS system would match against,
  including skills, technologies, certifications, and domain terms.
- Return ONLY valid JSON. No markdown code fences, no explanation.

Job Description Text:
{raw_text}"""

def parse_job_description(raw_text: str) -> Dict:
    client = _get_client()
    if not client:
        return _heuristic_jd_parse(raw_text)

    try:
        prompt = JD_USER_PROMPT.format(raw_text=raw_text[:8000])
        raw_response = _call_groq(client, JD_SYSTEM_PROMPT, prompt)
        result = _try_parse_json(raw_response)
        if result is not None:
            return _validate_jd_result(result)

        logger.warning("Groq JD parse: first attempt returned invalid JSON, retrying...")
        strict_prompt = (
            "Your previous response was not valid JSON. "
            "Return ONLY the raw JSON object, no markdown, no explanation, no code fences.\n\n"
            + prompt
        )
        raw_response = _call_groq(client, JD_SYSTEM_PROMPT, strict_prompt)
        result = _try_parse_json(raw_response)
        if result is not None:
            return _validate_jd_result(result)
    except Exception as exc:
        logger.error(f"Groq JD parsing failed: {exc}. Falling back to heuristic parser.")

    return _heuristic_jd_parse(raw_text)


def _heuristic_resume_parse(text: str) -> Dict:
    import re
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    phone_match = re.search(r'\(?\+?\d{1,4}\)?[\s\.-]?\d{3,5}[\s\.-]?\d{3,5}', text)
    linkedin_match = re.search(r'linkedin\.com/in/[\w\.-]+', text, re.IGNORECASE)
    github_match = re.search(r'github\.com/[\w\.-]+', text, re.IGNORECASE)

    # Simple tech skill extraction heuristics
    known_skills = [
        "python", "javascript", "typescript", "react", "fastapi", "django", "node.js",
        "express", "sql", "postgresql", "mongodb", "aws", "docker", "git", "c++", "java",
        "html", "css", "machine learning", "nlp", "pandas", "numpy", "scikit-learn"
    ]
    found_skills = [skill.title() for skill in known_skills if re.search(rf'\b{re.escape(skill)}\b', text, re.IGNORECASE)]

    # Action verbs heuristic
    verbs = ["developed", "built", "implemented", "designed", "created", "led", "managed", "optimized", "engineered", "automated"]
    found_verbs = [v.title() for v in verbs if re.search(rf'\b{re.escape(v)}\b', text, re.IGNORECASE)]

    name = text.splitlines()[0].strip() if text.splitlines() else "Candidate"
    if len(name) > 40 or len(name.split()) > 4:
        name = "Candidate"

    return _validate_resume_result({
        "name": name,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "linkedin": f"https://{linkedin_match.group(0)}" if linkedin_match else None,
        "github": f"https://{github_match.group(0)}" if github_match else None,
        "professional_summary": text[:300] if len(text) > 50 else "",
        "skills": list(set(found_skills)),
        "experience": [{"job_title": "Experience", "company": "", "description": text[:500]}],
        "education": [],
        "projects": [],
        "action_verbs": list(set(found_verbs)),
        "keywords": list(set(found_skills + found_verbs))
    })


def _heuristic_jd_parse(text: str) -> Dict:
    import re
    known_skills = [
        "python", "javascript", "typescript", "react", "fastapi", "django", "node.js",
        "sql", "postgresql", "mongodb", "aws", "docker", "git", "c++", "java",
        "machine learning", "nlp", "rest api"
    ]
    found = [s.title() for s in known_skills if re.search(rf'\b{re.escape(s)}\b', text, re.IGNORECASE)]

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    job_title = lines[0] if lines and len(lines[0]) < 50 else "Job Description"

    return _validate_jd_result({
        "job_title": job_title,
        "required_skills": found,
        "preferred_skills": [],
        "experience_required": "",
        "education_required": "",
        "key_responsibilities": lines[1:5] if len(lines) > 1 else [],
        "keywords": found
    })


def _validate_jd_result(result: dict) -> dict:
    defaults = {
        "job_title": "",
        "required_skills": [],
        "preferred_skills": [],
        "experience_required": "",
        "education_required": "",
        "key_responsibilities": [],
        "keywords": [],
    }
    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default
    return result


def _validate_resume_result(result: dict) -> dict:
    if not isinstance(result, dict):
        result = {}
    defaults = {
        "name": "",
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "professional_summary": "",
        "skills": [],
        "experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "action_verbs": [],
        "keywords": [],
    }
    for key, default in defaults.items():
        if key not in result or result[key] is None:
            result[key] = default
        if isinstance(default, list) and not isinstance(result[key], list):
            result[key] = default

    for exp in result.get("experience", []):
        if not isinstance(exp, dict):
            continue
        exp.setdefault("job_title", "")
        exp.setdefault("company", "")
        exp.setdefault("start_date", "")
        exp.setdefault("end_date", "")
        exp.setdefault("duration_months", 0)
        exp.setdefault("description", "")
        try:
            exp["duration_months"] = int(exp["duration_months"])
        except (ValueError, TypeError):
            exp["duration_months"] = 0

    for proj in result.get("projects", []):
        if not isinstance(proj, dict):
            continue
        proj.setdefault("title", "")
        proj.setdefault("description", "")
        proj.setdefault("technologies", [])

    return result



