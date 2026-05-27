@echo off
echo Starting Public Data Compliance System on port 8013...
cd /d "%~dp0"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8013 --reload
pause