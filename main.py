"""
main.py
-------
FastAPI backend for FinAgent. Exposes:
  POST /upload        - upload/reload a statement CSV
  POST /ask           - ask the agent a question
  GET  /transactions   - list all transactions
  GET  /summary        - quick summary without going through the LLM

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import shutil
from pathlib import Path

from app.db import init_db, get_all_transactions
from app.parser import load_statement
from app.agent import run_agent
from app.tools import get_spending_summary, detect_anomalies

app = FastAPI(title="FinAgent API")

UPLOAD_DIR = Path("sample_data")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.on_event("startup")
def startup():
    init_db()


class AskRequest(BaseModel):
    question: str


@app.post("/upload")
async def upload_statement(file: UploadFile = File(...)):
    dest = UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    count = load_statement(str(dest))
    return {"status": "ok", "transactions_loaded": count}


@app.post("/ask")
async def ask(request: AskRequest):
    answer = run_agent(request.question, verbose=False)
    return {"question": request.question, "answer": answer}


@app.get("/transactions")
async def transactions():
    return get_all_transactions()


@app.get("/summary")
async def summary(month: str = None):
    return get_spending_summary(month=month)


@app.get("/anomalies")
async def anomalies():
    return detect_anomalies()


@app.get("/")
async def root():
    return {"message": "FinAgent API is running. See /docs for endpoints."}
