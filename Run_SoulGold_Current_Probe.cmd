@echo off
setlocal
cd /d "%~dp0"
echo SOULGOLD - PRIVATE CURRENT-COPY GDB PROBE ONLY
echo.
echo This helper does not start mGBA or select any battle action.
echo Before opening: use TEST_COPY ROM/save, pause mGBA, enable local GDB server.
echo It needs independently reviewed PR28 observer bytes in tools\.
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 launcher not found. Install official Python 3 or run tools\run_current_copy_probe_local.py with Python.
  pause
  exit /b 2
)
py -3 "tools\run_current_copy_probe_local.py" --observer "tools\capture_original_request_rsp.py" --run-probe
if errorlevel 1 (
  echo The probe failed or produced an incomplete report. Check the private report only.
  pause
  exit /b 2
)
echo.
echo The report is LOCAL RESEARCH EVIDENCE ONLY, not gameplay certification.
echo Review SoulGold_Private_Probe_Reports before privately sharing anything.
pause