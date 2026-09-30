import streamlit as st

def render():
    
    # Landing page CSS
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #9333EA 100%);
            color: white;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(79, 70, 229, 0.3);
        }
        .main-header h1 {
            font-size: 2.8rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="main-header">
        <h1>🎯 ATS Resume Scorer & Candidate Shortlisting</h1>
        <h3>AI-Powered Resume Analysis & Smart Hiring Assistant</h3>
        <p>Analyze resumes, match with job descriptions, and shortlist top candidates instantly</p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Resume Scoring", use_container_width=True, type="primary"):
            st.session_state.current_view = 'scorer'
            st.rerun()
        
        if st.button("👥 Go to Candidate Shortlisting", use_container_width=True):
            st.session_state.current_view = 'batch_scorer'
            st.rerun()
    
    st.markdown("---")
    
    # Features Overview
    st.markdown("## ✨ Key Features")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 📊 ATS Scoring
        - Resume evaluation across multiple dimensions  
        - Formatting, keywords, content quality  
        - ATS compatibility check  
        """)
    
    with col2:
        st.markdown("""
        ### 🔍 Skill Validation
        - Verify real skills using AI  
        - Match skills with experience/projects  
        - Detect fake claims  
        """)
    
    with col3:
        st.markdown("""
        ### 👥 Candidate Shortlisting
        - Upload multiple resumes or ZIP  
        - AI ranks candidates automatically  
        - Get top candidates instantly  
        """)
    
    with col4:
        st.markdown("""
        ### 🔒 Privacy First
        - Runs locally (no external API)  
        - Secure data processing  
        - No data leakage  
        """)
    
    st.markdown("---")
    
    # How It Works
    st.markdown("## 🚀 How It Works")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        #### 1️⃣ Upload Resume(s)
        Single or multiple resumes (PDF, DOCX, ZIP)
        """)
    
    with col2:
        st.markdown("""
        #### 2️⃣ AI Processing
        BERT-based semantic analysis of resume & JD
        """)
    
    with col3:
        st.markdown("""
        #### 3️⃣ Smart Matching
        Skill matching + similarity scoring
        """)
    
    with col4:
        st.markdown("""
        #### 4️⃣ Shortlist Candidates
        Ranked leaderboard with insights & feedback
        """)