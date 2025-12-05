
# DeepLynctus– Intelligent Code Quality & Bug Risk Analyzer (AIML + NLP)

DeepLynctus is an AI-powered system that scans a source-code repository to detect bug-prone files, code smells, technical debt risk, and provides smart refactoring suggestions.  
It combines static analysis, ML prediction, and NLP patterns, along with visual dashboards and PDF reports.

---
## Prerequisites

- **Node.js** 18+ & npm
- **Python** 3.10+
- **MongoDB** (optional – uses in-memory DB by default)

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

<<<<<<< HEAD
### Test Endpoints
```powershell
# Health check
curl http://localhost:8000/

# Queue a repository
curl -X POST http://localhost:8000/upload/repo -H "Content-Type: application/json" -d '{"source_type":"github","source_ref":"https://github.com/org/repo"}'

# Start scan
curl -X POST http://localhost:8000/scan/project -H "Content-Type: application/json" -d '{"project_id":"demo"}'

# Get metrics
curl http://localhost:8000/metrics/demo

# Get risks
curl http://localhost:8000/risks/demo

# Get suggestions
curl http://localhost:8000/suggestions/file123

# Export report
curl -X POST http://localhost:8000/report/export -H "Content-Type: application/json" -d '{"project_id":"demo","format":"pdf"}'
```

---

## Frontend (React + Tailwind)

### Setup
```powershell
Set-Location "c:\Users\JUNAID ASAD KHAN\bug risk NLP\frontend"
=======
# Frontend
cd frontend
>>>>>>> e552d18776eb64ce6968912accc4050c5e5fcfd7
npm install
npm start
MongoDB required locally or cloud.

<<<<<<< HEAD
Open http://localhost:5173

---

## 📁 Project Structure

```
codesensex/
├── backend/
│   ├── main.py                 # FastAPI application entry
│   ├── controllers/            # Route handlers
│   ├── services/               # Business logic & database
│   ├── ml/                     # Machine learning models
│   ├── parsers/                # Code parsers (Python AST)
│   ├── config/                 # MongoDB configuration
│   └── models/                 # Pydantic schemas
│
└── frontend/
    └── src/
        ├── main.jsx            # App shell & navigation
        ├── components/         # Reusable UI components
        ├── pages/              # Page components
        └── services/           # API client
```

---

## 🎨 UI Theme

- **Dark Mode** – Deep grey background (#09090b)
- **Glassmorphism** – Frosted glass effect cards
- **Teal/Cyan Accents** – Gradient highlights
- **Framer Motion** – Smooth animations

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload/repo` | POST | Queue a GitHub repository |
| `/scan/project/{id}/start` | POST | Start analysis |
| `/metrics/{project_id}` | GET | Get file metrics |
| `/risks/{project_id}` | GET | Get risk scores |
| `/suggestions/{file_id}` | GET | Get AI suggestions |
| `/report/export` | POST | Generate PDF report |

---

## 📄 License

MIT © 2024 CodeSenseX
=======
📜 Final Note
DeepLynctus helps engineering teams find weak code areas before they become real bugs.
It reflects strong knowledge of:

ML,

static code analysis,

software principles,

NLP,

visualization.
>>>>>>> e552d18776eb64ce6968912accc4050c5e5fcfd7
