@echo off
setlocal
set "ROOT=%~dp0"
set "PYTHONPATH=%ROOT%"
if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" -m ase_deliver %*
) else (
  py -3 -m ase_deliver %*
)

