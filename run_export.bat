@echo off
echo Starting export...
python -u export_questions_v2.py > export_log.txt 2>&1
echo Finished export with exit code %errorlevel% >> export_log.txt
