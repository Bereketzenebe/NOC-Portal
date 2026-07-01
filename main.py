"""
Safaricom Ethiopia NOC Portal — Local FastAPI Server
Run: uvicorn main:app --reload --port 8000
"""
import csv, io, os, re
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent
app  = FastAPI(title="Safaricom NOC Portal")

# ── CSV helper ────────────────────────────────────────────────────────────────
def read_csv(filename: str) -> list[dict]:
    path = BASE / filename
    if not path.exists():
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: v for k, v in row.items()})
    return rows

# ── Data injection helper ─────────────────────────────────────────────────────
import json as _json

def inject_and_send(html_file: str, var_name: str, data) -> HTMLResponse:
    html = (BASE / html_file).read_text(encoding="utf-8")
    tag  = f"<script>window.{var_name} = {_json.dumps(data, ensure_ascii=False)};</script>"
    html = html.replace("</head>", tag + "\n</head>", 1)
    return HTMLResponse(content=html)

# ── HTML pages with injected data ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
@app.get("/index.html", response_class=HTMLResponse)
async def dashboard():
    return inject_and_send("index.html", "__DASHBOARD_DATA__", {
        "networkKPIs": read_csv("kpi_data.csv"),
        "nocMatrix":   read_csv("matrix_data.csv"),
        "regions":     read_csv("regional_data.csv"),
        "chronic":     read_csv("chronic_data.csv"),
    })

@app.get("/login.html", response_class=HTMLResponse)
async def login_page():
    return HTMLResponse((BASE / "login.html").read_text(encoding="utf-8"))

@app.get("/roster.html", response_class=HTMLResponse)
async def roster_page():
    return inject_and_send("roster.html", "__ROSTER_DATA__", read_csv("roster.csv"))

@app.get("/oncall.html", response_class=HTMLResponse)
async def oncall_page():
    return inject_and_send("oncall.html", "__ONCALL_DATA__", read_csv("oncall.csv"))

@app.get("/process.html", response_class=HTMLResponse)
async def process_page():
    return inject_and_send("process.html", "__PROCESS_DATA__", read_csv("process_docs.csv"))

@app.get("/handover.html", response_class=HTMLResponse)
async def handover_page():
    return HTMLResponse((BASE / "handover.html").read_text(encoding="utf-8"))

# ── JSON API endpoints (AJAX fallback) ────────────────────────────────────────
@app.get("/api/data")
async def api_data():
    return {
        "networkKPIs": read_csv("kpi_data.csv"),
        "nocMatrix":   read_csv("matrix_data.csv"),
        "regions":     read_csv("regional_data.csv"),
        "chronic":     read_csv("chronic_data.csv"),
    }

@app.get("/api/roster")
async def api_roster():
    return {"roster": read_csv("roster.csv")}

@app.get("/api/oncall")
async def api_oncall():
    return {"oncall": read_csv("oncall.csv")}

@app.get("/api/process-docs")
async def api_process_docs():
    return {"docs": read_csv("process_docs.csv")}

# ── Login endpoint ─────────────────────────────────────────────────────────────
USERS = {
    "admin":    {"password": "Admin@NOC2024",  "role": "admin",    "displayName": "Admin User"},
    "operator": {"password": "Operator@2024",  "role": "operator", "displayName": "NOC Operator"},
    "guest":    {"password": "Guest@2024",      "role": "guest",    "displayName": "Guest Viewer"},
}

@app.post("/api/v1/login")
async def login(request: Request):
    body = await request.json()
    username = (body.get("username") or "").lower()
    password = body.get("password") or ""
    user = USERS.get(username)
    if user and user["password"] == password:
        return {"status": "success", "username": username,
                "role": user["role"], "displayName": user["displayName"]}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# ── Static files (CSVs, PDFs, etc.) ───────────────────────────────────────────
app.mount("/docs", StaticFiles(directory=str(BASE / "docs")), name="docs")
