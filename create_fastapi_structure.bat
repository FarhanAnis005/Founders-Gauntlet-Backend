@echo off
:: This script creates the directory structure for the Shark Tank AI Pitch project.

:: Create the root project folder


:: Create the main 'app' directory and its subdirectories
echo Creating 'app' structure...
mkdir app
mkdir app\api
mkdir app\api\v1
mkdir app\api\v1\endpoints
mkdir app\agent
mkdir app\background
mkdir app\core
mkdir app\db
mkdir app\db\models
mkdir app\schemas
mkdir app\security
mkdir app\services

:: Create the 'tests' directory
mkdir tests

:: Create all the Python files and __init__.py files
echo Creating Python files...
type nul > app\__init__.py
type nul > app\main.py

type nul > app\api\__init__.py
type nul > app\api\api_router.py
type nul > app\api\v1\__init__.py
type nul > app\api\v1\endpoints\__init__.py
type nul > app\api\v1\endpoints\pitches.py

type nul > app\agent\__init__.py
type nul > app\agent\rag.py
type nul > app\agent\shark_tank_agent.py

type nul > app\background\__init__.py
type nul > app\background\tasks.py

type nul > app\core\__init__.py
type nul > app\core\celery_app.py
type nul > app\core\config.py

type nul > app\db\__init__.py
type nul > app\db\session.py
type nul > app\db\models\__init__.py
type nul > app\db\models\pitch.py

type nul > app\schemas\__init__.py
type nul > app\schemas\pitch.py

type nul > app\security\__init__.py
type nul > app\security\clerk.py

type nul > app\services\__init__.py
type nul > app\services\deck_processor.py
type nul > app\services\livekit_service.py
type nul > app\services\pitch_service.py

:: Create root-level project files
echo Creating project configuration files...
type nul > .env
type nul > .gitignore
type nul > requirements.txt
type nul > README.md

echo.
echo Project structure 'shark-tank-backend' created successfully! 🎉
cd ..
pause