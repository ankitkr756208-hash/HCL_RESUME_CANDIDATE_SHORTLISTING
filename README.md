# ATS Resume Scorer --- AI Resume Screening & Candidate Shortlisting

An AI-powered Applicant Tracking System (ATS) that evaluates resumes
against a job description, highlights relevant and missing skills, and
ranks candidates to help recruiters review applications more
efficiently.

## Table of Contents

-   [Overview](#overview)
-   [Features](#features)
-   [Project Structure](#project-structure)
-   [Technology Stack](#technology-stack)
-   [How It Works](#how-it-works)
-   [Installation](#installation)
-   [Configuration](#configuration)
-   [Run the Application](#run-the-application)
-   [API Endpoints](#api-endpoints)
-   [Bulk Shortlisting](#bulk-shortlisting)
-   [Model Evaluation](#model-evaluation)
-   [Troubleshooting](#troubleshooting)
-   [Responsible Use](#responsible-use)
-   [Future Improvements](#future-improvements)

## Overview

ATS Resume Scorer combines semantic text embeddings, resume parsing, and
job-description matching in a web application. Recruiters can screen one
resume or process a batch of resumes and review candidates in a ranked
leaderboard.

The project includes a FastAPI backend for API services and a Streamlit
frontend for the user interface. A fine-tuned SentenceTransformer model
is used for semantic similarity where the trained model is available.

> **Important:** Similarity scores are decision-support signals, not
> proof that a candidate is qualified. Recruiters should review the
> original resume and use consistent, job-related criteria.

## Features

-   **Single resume screening:** Paste resume text or upload a supported
    resume file.
-   **Job-description matching:** Compare a resume with the target job
    description.
-   **Match score and category:** Present a normalized score and a HIGH
    / MEDIUM / LOW category.
-   **Skill comparison:** Show detected matched skills and missing
    skills when supported by the configured skill matcher.
-   **Batch shortlisting:** Upload multiple resume files and rank
    candidates by match score.
-   **ZIP upload:** Process supported resumes stored inside a ZIP
    archive.
-   **Folder mode:** Scan a folder path accessible to the backend, where
    this mode is enabled.
-   **Leaderboard:** Sort candidates by score and inspect the top
    candidates.
-   **CSV export:** Download a shortlist report for further review.
-   **EDA and model insights:** View available dataset statistics and
    model-comparison metrics.
-   **API documentation:** Explore and test endpoints through FastAPI's
    Swagger UI.

Supported formats may vary by mode and parser configuration. The
folder/ZIP implementation described for this project supports PDF, DOCX,
and TXT; verify the current parser before relying on additional formats.

## Project Structure

The repository may contain additional views, notebooks, and utilities.
The core application structure is expected to look similar to:

``` text
RESUME_ATS-main/
├── backend/
│   ├── main.py
│   ├── model_service.py
│   └── file_parser.py
├── frontend/
│   ├── streamlit_app.py
│   ├── services/
│   │   └── api_client.py
│   └── views/
├── jupyter notebooks/
│   ├── resume_short.ipynb
│   ├── BERT_EMBEDING.ipynb
│   └── Fine_Tunning.ipynb
├── tests/
├── models/
│   └── finetuned-bert/
├── requirements.txt
├── .gitignore
└── README.md
```

Your actual folder and notebook names may differ. Keep large model
weights and private datasets out of Git unless the repository is
intentionally configured to store them.

## Technology Stack

-   **Python** --- application and model code
-   **FastAPI** --- backend REST API
-   **Streamlit** --- interactive frontend
-   **SentenceTransformers / BERT** --- semantic embeddings and
    similarity
-   **pypdf** --- PDF text extraction
-   **python-docx** --- DOCX text extraction
-   **Pandas** --- tabular data and CSV reports
-   **Scikit-learn / evaluation utilities** --- model evaluation where
    used
-   **Jupyter Notebook** --- EDA, embeddings, and fine-tuning
    experiments

## How It Works

1.  A recruiter supplies a job description.
2.  The parser extracts text from each resume.
3.  The model encodes the job description and resume text into
    embeddings.
4.  The application calculates semantic similarity and, when enabled,
    combines it with skill matching.
5.  Candidates are sorted by their resulting score.
6.  The frontend displays scores, categories, skills, and a downloadable
    report.

### Default score categories

The folder/ZIP workflow was designed with these thresholds:

  Category           Similarity score
  ---------- ------------------------
  HIGH                      `>= 0.75`
  MEDIUM       `>= 0.50` and `< 0.75`
  LOW                        `< 0.50`

These thresholds are configurable business rules, not universally
validated hiring standards. Confirm that the score returned by the model
is on the expected scale before using these cutoffs.

## Installation

### 1. Clone the repository

``` bash
git clone https://github.com/ankitkr756208-hash/HCL_RESUME_CANDIDATE_SHORTLISTING.git
cd HCL_RESUME_CANDIDATE_SHORTLISTING/RESUME_ATS-main
```

If the application files are already in your local folder, open a
terminal in the directory containing `backend/` and `frontend/`.

### 2. Create and activate a virtual environment

**Windows PowerShell:**

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

``` bat
py -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If a dependency is missing, install it only after checking the imports
used by your current code. Common parser dependencies include:

``` bash
pip install fastapi "uvicorn[standard]" streamlit sentence-transformers pypdf python-docx pandas python-multipart
```

## Configuration

If the application uses external services or API keys, configure them
using environment variables. Do not commit secrets to Git.

1.  Check whether the repository provides a `.env.example` file.
2.  Create a local `.env` file if the application expects one.
3.  Add the required variables using the names referenced in your code.
4.  Add `.env` to `.gitignore`.

For example:

``` text
# Example only — use the exact variable names required by your code.
GROQ_API_KEY=your_api_key_here
```

The Groq key is only needed if your current implementation calls the
Groq API. The core semantic-matching workflow may not require it.

## Run the Application

Open **two separate terminals** from the project root.

### Terminal 1 --- Start FastAPI

``` bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

API health check, if enabled:

``` text
http://127.0.0.1:8000/health
```

Interactive API documentation:

``` text
http://127.0.0.1:8000/docs
```

### Terminal 2 --- Start Streamlit

``` bash
streamlit run frontend/streamlit_app.py
```

Open the local address printed by Streamlit, commonly:

``` text
http://localhost:8501
```

If your repository uses a different entry point, run the Streamlit file
that contains the main application navigation.

## API Endpoints

The following endpoints are described by the project implementation.
Confirm their availability in `backend/main.py` or the registered
routers.

  -------------------------------------------------------------------------
  Method                  Endpoint                  Purpose
  ----------------------- ------------------------- -----------------------
  `GET`                   `/health`                 Check backend/model
                                                    readiness

  `POST`                  `/api/score`              Score one resume
                                                    against a job
                                                    description

  `POST`                  `/api/shortlist`          Rank multiple uploaded
                                                    candidates

  `GET`                   `/api/stats`              Return dataset and
                                                    model statistics

  `POST`                  `/api/shortlist-folder`   Process supported
                                                    resumes from a
                                                    backend-accessible
                                                    folder

  `POST`                  `/api/shortlist-zip`      Process supported
                                                    resumes inside a ZIP
                                                    upload

  `POST`                  `/api/v1/batch-analyze`   Batch analysis route
                                                    used by an alternate
                                                    batch-processing
                                                    workflow, if registered
  -------------------------------------------------------------------------

Not every route above necessarily exists in every branch or version. The
registered FastAPI routes are the source of truth. Use `/docs` to see
the endpoints available in your running application.

### Example folder request

For an implementation that accepts JSON input:

``` json
{
  "folder_path": "path/to/resumes",
  "jd": "Paste the job description here"
}
```

Use a folder path that is accessible to the **backend machine**. In a
deployed environment, a path on the recruiter's personal computer will
not automatically be accessible to the server.

## Bulk Shortlisting

1.  Open the Streamlit application.
2.  Select the batch/bulk shortlisting view.
3.  Paste or upload the job description.
4.  Choose one of the supported input modes:
    -   Upload multiple resume files.
    -   Upload a ZIP archive containing resumes.
    -   Enter a folder path, if folder mode is enabled.
5.  Start processing.
6.  Review the ranked leaderboard and candidate details.
7.  Filter the top candidates and download the CSV report.

For ZIP files, use only resumes you are authorized to process. Avoid
including unrelated files or sensitive information that is not required
for screening.

## Model Evaluation

The project notes report that fine-tuning reduced MAE from `0.2096` to
`0.1360` in the recorded experiment (a reported relative improvement of
approximately **35.1%**). Treat this as an experiment-specific result,
not a guarantee of real-world hiring accuracy.

For a meaningful evaluation:

-   Use a held-out test set that was not used for fine-tuning.
-   Document how ground-truth relevance labels were created.
-   Compare the base and fine-tuned models on the same split.
-   Report suitable metrics such as MAE/RMSE for score prediction and
    Precision@K / Recall@K for ranking.
-   Check for data leakage, duplicate resumes, and imbalanced labels.
-   Evaluate performance across relevant candidate groups and review
    potential bias before real hiring use.

## Troubleshooting

### `AttributeError: module 'frontend.services.api_client' has no attribute 'batch_analyze_resumes'`

-   Confirm that `batch_analyze_resumes()` is defined in
    `frontend/services/api_client.py`.
-   Confirm that the caller imports it from the correct module and uses
    the correct function name.
-   Stop and restart Streamlit after changing Python modules:

``` bash
# Stop the running process with Ctrl+C, then run:
streamlit run frontend/streamlit_app.py
```

### Model files are missing

Check that the configured model directory exists and contains the
required saved model files. If the model must be trained locally, run
the repository's training script or notebook according to its
instructions.

### Resume text is empty

Some PDFs contain scanned images rather than selectable text. Text
extraction may return little or no content for such files. Consider
adding OCR support and showing a clear warning when extracted text is
empty.

### Folder path does not work

-   Verify the path exists on the backend machine.
-   Check read permissions.
-   Use the correct path format for your operating system.
-   If the app is deployed, use an uploaded ZIP instead of a path from
    your local computer.

### Port already in use

Choose another port, for example:

``` bash
uvicorn backend.main:app --reload --port 8001
```

If you change the backend port, update the API base URL in the Streamlit
configuration.

## Responsible Use

-   Use resume data only with appropriate authorization and safeguards.
-   Do not use protected characteristics or proxies for them as ranking
    criteria.
-   Treat missing keywords as a prompt for human review, not automatic
    evidence that a candidate lacks a skill.
-   Keep uploaded resumes, extracted text, logs, and exports secure.
-   Set appropriate file-size limits and validate ZIP contents before
    extraction.
-   For production deployment, add authentication, access control, rate
    limits, upload limits, monitoring, and retention/deletion policies.
-   Ensure a human makes final hiring decisions and candidates are
    assessed using job-related criteria.

## Future Improvements

-   OCR support for scanned resumes.
-   Background jobs and processing status for large batches.
-   Caching and batch embedding to reduce repeated model work.
-   Recruiter authentication and role-based access control.
-   Persistent screening history with configurable retention.
-   Explainable score breakdown and configurable skill weights.
-   Automated tests for parsers, API routes, ZIP edge cases, and ranking
    order.
-   Docker-based deployment and CI checks.

## Author

**Ankit Kumar**\
B.Tech, Computer Science & Engineering

Project: **HCL Resume Candidate Shortlisting --- ATS Resume Scorer**
