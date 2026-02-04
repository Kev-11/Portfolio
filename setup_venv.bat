@echo off
echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Initializing database...
python -c "from backend.database import init_db; init_db()"

echo.
echo Setup complete!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate.bat
echo.
echo To start the backend server, run:
echo   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo To deactivate the virtual environment, run:
echo   deactivate
echo.
pause
