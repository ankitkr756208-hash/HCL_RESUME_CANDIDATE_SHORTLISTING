import io
import csv
from typing import Optional, List, Dict, Any

import requests
import streamlit as st
import pandas as pd

from frontend.services.api_client import batch_analyze_resumes


def _show_error(exc: Exception) -> None:
    if isinstance(exc, requests.ConnectionError):
        st.error("Could not reach backend server. Make sure `uvicorn backend.main:app` is running on port 8000.")
    elif isinstance(exc, requests.HTTPError) and exc.response is not None:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except Exception:
            detail = exc.response.text
        st.error(f"Backend Error ({exc.response.status_code}): {detail}")
    else:
        st.error(f"Error: {exc}")


def _generate_csv(candidates: List[Dict[str, Any]]) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Rank", "Candidate Name", "File Name", "Status",
        "JD Match Score (%)", "ATS Score", "Matched Skills", "Missing Skills"
    ])

    for c in candidates:
        writer.writerow([
            c.get("rank"),
            c.get("candidate_name"),
            c.get("filename"),
            c.get("status"),
            f"{c.get('jd_match_pct', 0):.1f}%",
            f"{c.get('ats_score', 0):.1f}",
            ", ".join(c.get("matched_skills", [])),
            ", ".join(c.get("missing_skills", [])),
        ])

    return output.getvalue().encode("utf-8")


def render() -> None:
    st.title("👥 Batch Candidate Shortlisting & Ranking")
    st.markdown(
        "Upload multiple resumes or a `.zip` folder along with a Job Description "
        "to automatically score, rank, and shortlist top candidates."
    )

    access_token = st.session_state.get("access_token")
    if not access_token:
        st.warning("⚠️ Please sign in from the sidebar to use Batch Candidate Shortlisting.")
        return

    st.markdown("---")

    # Step 1: Input method and file uploaders
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📂 1. Upload Resumes")
        upload_mode = st.radio(
            "Select upload method:",
            ["Drag & Drop Multiple Resumes", "Upload ZIP Archive (.zip)"],
            horizontal=True,
            key="batch_upload_mode",
        )

        resume_files: List[Any] = []
        zip_file: Optional[Any] = None

        if upload_mode == "Upload ZIP Archive (.zip)":
            zip_file = st.file_uploader(
                "Choose ZIP file containing candidate resumes",
                type=["zip"],
                help="Upload a .zip file containing up to 50+ PDF/DOCX resumes.",
                key="zip_uploader",
            )
            if zip_file:
                st.success(f"✅ Loaded ZIP archive: **{zip_file.name}** ({zip_file.size / 1024:.1f} KB)")
        else:
            resume_files = st.file_uploader(
                "Choose multiple resume files",
                type=["pdf", "docx", "doc", "txt"],
                accept_multiple_files=True,
                help="Select 2 to 50+ candidate resume files.",
                key="multi_file_uploader",
            )
            if resume_files:
                st.success(f"✅ Loaded {len(resume_files)} resume file(s).")

    with col2:
        st.markdown("### 📋 2. Job Description")
        jd_input_method = st.radio(
            "JD Input Method:",
            ["Paste Text", "Upload .txt File"],
            horizontal=True,
            key="batch_jd_method",
        )

        jd_text = ""
        if jd_input_method == "Upload .txt File":
            jd_file = st.file_uploader("Upload Job Description (.txt)", type=["txt"], key="batch_jd_file")
            if jd_file:
                jd_text = jd_file.getvalue().decode("utf-8", errors="ignore")
                st.success(f"✅ JD Loaded: {len(jd_text)} characters")
        else:
            jd_text = st.text_area(
                "Paste Job Description here:",
                height=180,
                placeholder="Paste the target job description (skills, responsibilities, requirements)...",
                key="batch_jd_text",
            )
            if jd_text:
                st.caption(f"Length: {len(jd_text)} characters")

    st.markdown("---")

    # Action Button
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        start_batch = st.button("🚀 Shortlist & Rank Candidates", type="primary", use_container_width=True)

    if start_batch:
        if not zip_file and not resume_files:
            st.error("Please upload resumes or a ZIP archive to begin.")
            return

        try:
            with st.spinner("Processing candidate batch... Parsing resumes & computing semantic JD match scores."):
                results = batch_analyze_resumes(
                    resume_files=resume_files,
                    zip_file=zip_file,
                    access_token=access_token,
                    job_description=jd_text,
                )
                st.session_state["batch_results"] = results
                st.success(f"✅ Batch completed! Processed {results.get('total_candidates', 0)} candidates.")
        except requests.RequestException as exc:
            _show_error(exc)
            return

    # Render Batch Results Dashboard if present in session state
    batch_data = st.session_state.get("batch_results")
    if not batch_data:
        return

    st.markdown("---")
    st.markdown("## 📊 Candidate Shortlist Summary")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("👥 Total Processed", batch_data.get("total_candidates", 0))
    m2.metric("🟢 Shortlisted (>=75%)", batch_data.get("shortlisted_count", 0))
    m3.metric("🟡 Under Review (55-74%)", batch_data.get("under_review_count", 0))
    m4.metric("🔴 Not Suitable (<55%)", batch_data.get("not_suitable_count", 0))
    m5.metric("🏆 Top Match Score", f"{batch_data.get('top_score', 0):.1f}%")

    candidates = batch_data.get("candidates", [])
    if not candidates:
        st.info("No candidates were processed in this batch.")
        return

    st.markdown("---")

    # Filters and Search
    st.markdown("### 🏆 Candidate Leaderboard")
    filter_col1, filter_col2, filter_col3 = st.columns([1, 1, 2])

    with filter_col1:
        status_filter = st.selectbox(
            "Filter by Status:",
            ["All Candidates", "Shortlisted", "Under Review", "Not Suitable"],
        )

    with filter_col2:
        sort_by = st.selectbox(
            "Sort by:",
            ["Rank / Match Score (High to Low)", "ATS Score (High to Low)", "Candidate Name"],
        )

    with filter_col3:
        search_query = st.text_input("🔍 Search candidate or skill:", "").strip().lower()

    # Filter candidates
    filtered = candidates
    if status_filter != "All Candidates":
        filtered = [c for c in filtered if c.get("status") == status_filter]

    if search_query:
        filtered = [
            c for c in filtered
            if search_query in c.get("candidate_name", "").lower()
            or search_query in c.get("filename", "").lower()
            or any(search_query in s.lower() for s in c.get("matched_skills", []))
        ]

    if sort_by == "ATS Score (High to Low)":
        filtered = sorted(filtered, key=lambda x: x.get("ats_score", 0), reverse=True)
    elif sort_by == "Candidate Name":
        filtered = sorted(filtered, key=lambda x: x.get("candidate_name", "").lower())
    else:
        filtered = sorted(filtered, key=lambda x: x.get("rank", 999))

    # Leaderboard Table Display
    table_data = []
    for c in filtered:
        status = c.get("status")
        badge = "🟢" if status == "Shortlisted" else "🟡" if status == "Under Review" else "🔴"
        table_data.append({
            "Rank": f"#{c.get('rank')}",
            "Status": f"{badge} {status}",
            "Candidate Name": c.get("candidate_name"),
            "JD Match %": f"{c.get('jd_match_pct', 0):.1f}%",
            "ATS Score": f"{c.get('ats_score', 0):.1f}/100",
            "Top Matched Skills": ", ".join(c.get("matched_skills", [])[:5]),
            "File Name": c.get("filename"),
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Export Button
    st.markdown("### 📥 Export Shortlist Data")
    csv_bytes = _generate_csv(candidates)
    st.download_button(
        "📄 Download Complete Shortlist Leaderboard (.CSV)",
        data=csv_bytes,
        file_name="candidate_shortlist_leaderboard.csv",
        mime="text/csv",
        type="primary",
        use_container_width=False,
    )

    st.markdown("---")

    # Detailed Candidate Inspector
    st.markdown("### 🔍 Candidate Detail Inspector")
    candidate_names = [f"#{c.get('rank')} — {c.get('candidate_name')} ({c.get('filename')})" for c in candidates]
    selected_candidate_str = st.selectbox("Select Candidate to Inspect:", candidate_names)

    if selected_candidate_str:
        selected_idx = candidate_names.index(selected_candidate_str)
        cand = candidates[selected_idx]

        st.markdown(f"#### 👤 Candidate: **{cand.get('candidate_name')}**")
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("JD Match Score", f"{cand.get('jd_match_pct', 0):.1f}%")
        sc2.metric("Overall ATS Score", f"{cand.get('ats_score', 0):.1f}/100")
        sc3.markdown(f"**Status:** `{cand.get('status')}`")

        c_left, c_right = st.columns(2)
        with c_left:
            st.markdown("**✅ Matched Skills & Strengths:**")
            for skill in cand.get("matched_skills", []):
                st.markdown(f"- ✅ `{skill}`")
            if cand.get("top_strengths"):
                st.markdown("**Key Strengths:**")
                for strg in cand["top_strengths"]:
                    st.markdown(f"- 🌟 {strg}")

        with c_right:
            st.markdown("**⚠️ Missing Skills / Keywords:**")
            for m_skill in cand.get("missing_skills", []):
                st.markdown(f"- ❌ `{m_skill}`")
