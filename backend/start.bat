@echo off
set PYTHONPATH=%~dp0src
cd /d %~dp0src
python -m uvicorn main:app --host 0.0.0.0 --port 8001
