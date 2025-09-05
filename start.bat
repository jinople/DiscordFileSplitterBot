@echo off

echo Starting FileSplitterBot...
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Launching main.py...
python main.py

pause