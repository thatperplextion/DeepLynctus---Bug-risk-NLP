# CodeSenseX – Intelligent Code Quality & Bug Risk Analyzer

## Backend (FastAPI)

### Setup
```powershell
Set-Location "c:\Users\JUNAID ASAD KHAN\bug risk NLP\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Test
```powershell
curl http://localhost:8000/
curl -X POST http://localhost:8000/upload/repo -H "Content-Type: application/json" -d '{"source_type":"github","source_ref":"https://github.com/org/repo"}'
curl -X POST http://localhost:8000/scan/project -H "Content-Type: application/json" -d '{"project_id":"demo"}'
curl http://localhost:8000/metrics/demo
curl http://localhost:8000/risks/demo
curl http://localhost:8000/suggestions/file123
curl -X POST http://localhost:8000/report/export -H "Content-Type: application/json" -d '{"project_id":"demo","format":"pdf"}'
```

## Frontend (React + Tailwind)

### Setup
```powershell
Set-Location "c:\Users\JUNAID ASAD KHAN\bug risk NLP\frontend"
npm install
npm run dev
```

Open http://localhost:5173
