@echo off
setlocal
REM DoE-Assist: one-click closed loop (extract -> train -> recommend)

REM --- Editable defaults ---
set "TEXT=Protein X shows stability near pH 7; aggregation decreases near 45 C at 10 mg/mL."
set "OUT=ml_engine\output\windows.json"
set "STORE=literature_mining\storage\structured_store.jsonl"
set "PH_LO=3"
set "PH_HI=9"
set "TEMP_LO=10"
set "TEMP_HI=70"
set "CONC_LO=1"
set "CONC_HI=50"
set "PROB=0.7"

REM --- Move to project root ---
pushd "%~dp0\.."

REM Ensure output dir exists
if not exist "ml_engine\output" mkdir "ml_engine\output"

REM Run closed loop
python scripts\run_closed_loop.py ^
  --text "%TEXT%" ^
  --out "%OUT%" ^
  --store "%STORE%" ^
  --ph %PH_LO% %PH_HI% ^
  --temp %TEMP_LO% %TEMP_HI% ^
  --conc %CONC_LO% %CONC_HI% ^
  --prob-threshold %PROB%

set ERR=%ERRORLEVEL%
if not "%ERR%"=="0" (
  echo ❌ Failed with exit code %ERR%
  popd
  exit /b %ERR%
)

echo ✅ Saved recommended windows -> %OUT%
type "%OUT%"
popd
exit /b 0