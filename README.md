# DeepLynctus– Intelligent Code Quality & Bug Risk Analyzer (AIML + NLP)

DeepLynctus is an AI-powered system that scans a source-code repository to detect bug-prone files, code smells, technical debt risk, and provides smart refactoring suggestions.  
It combines static analysis, ML prediction, and NLP patterns, along with visual dashboards and PDF reports.

---

## 🚀 Features

### ✔ Code Analysis
- Scan GitHub repo or ZIP
- Auto language detection
- Extract code metrics:
  - LOC, complexity, nesting depth
  - Duplicate blocks
  - Comment density

### ✔ Bug-Risk Prediction (ML)
- Risk score (0–100)
- Safe / Warning / High-Risk levels
- Feature importance analysis

### ✔ NLP-Based Smell Detection
- Long functions
- Bad naming
- Hard-coded secrets
- Deep nesting
- Low cohesion

### ✔ AI Refactor Suggestions
- Cleaner design
- Naming fixes
- Modularity recommendations
- Best-practice patterns

### ✔ Dashboards
- Risk heatmap
- Top risky files
- Complexity vs risk graph
- Smell distribution
- Code-quality score

### ✔ PDF Summary Report
- Risk overview
- Top hotspots
- Improvement actions

---

## 🏗 System Architecture

Frontend (React)
↓
Backend (FastAPI)
↓
Repo Processor → Static Analyzer → Metrics Builder
↓
ML Risk Engine + NLP Smells
↓
MongoDB (Insights)
↓
Dashboards & PDF Report

yaml
Copy code

---

## 🔧 Tech Stack

- **Backend:** FastAPI (Python)
- **Frontend:** React + Tailwind
- **ML:** scikit-learn / XGBoost
- **Parsing:** Python AST / Tree-Sitter
- **DB:** MongoDB
- **Repo:** GitPython
- **Charts:** Recharts / Chart.js

---

## 🧮 Bug Risk Model

**Inputs:**  
LOC, complexity, nesting, function count, duplication ratio, comments ratio  

**Output:**  
0–35 → Safe
36–70 → Medium Risk
71–100 → High Risk

yaml
Copy code

Most critical metric: **Precision**  
(to avoid false high-risk flags)

---

## 🗄 Database Collections

- `projects`
- `file_metrics`
- `code_smells`
- `risk_scores`

Stores repo data, metrics, smell reports, and ML scores.

---

## 🛠 Main API Endpoints

| Method | Endpoint | Purpose |
|--------|---------|--------|
| POST | `/upload/repo` | Submit repo or zip |
| POST | `/scan/project/:id` | Start analysis |
| GET | `/metrics/:id` | Code metrics |
| GET | `/risks/:id` | Risk scores |
| GET | `/suggestions/:file` | Refactor tips |
| GET | `/report/export/:id` | PDF report |

---

## 📁 Suggested Folder Structure

backend/
ml/
parsers/
services/
reports/

frontend/
components/
pages/
charts/

yaml
Copy code

---

## 🖥 Dashboards

- Risk heatmap
- File-risk ranking
- Complexity-vs-risk graph
- Code smell stats
- Overall quality score

---

## 🧩 Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
MongoDB required locally or cloud.

📜 Final Note
DeepLynctus helps engineering teams find weak code areas before they become real bugs.
It reflects strong knowledge of:

ML,

static code analysis,

software principles,

NLP,

visualization.
