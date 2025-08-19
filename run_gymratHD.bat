@echo off
title gymratHD - Professional Setup
color 0F

echo.
echo ================================================================
echo   GYMRATHD - PROFESSIONAL INSTALLATION
echo   The Ultimate Mike Mentzer Training and Nutrition Tracker
echo ================================================================
echo   Created by: github.com/barebonesjones
echo ================================================================
echo.

echo [INFO] Starting installation...
echo.

:: Step 1: Check Python
echo [STEP 1/6] Checking Python...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from python.org
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo [OK] Python detected
echo.

:: Step 2: Check files
echo [STEP 2/6] Checking required files...
if not exist "gymratHD.py" (
    echo [ERROR] gymratHD.py not found!
    pause
    exit /b 1
)
echo [OK] gymratHD.py

if not exist "food_database.json" (
    echo [ERROR] food_database.json not found!
    pause
    exit /b 1
)
echo [OK] food_database.json

if not exist "create_logo.py" (
    echo [WARNING] create_logo.py not found - will skip logo creation
) else (
    echo [OK] create_logo.py
)
echo.

:: Step 3: Create folders
echo [STEP 3/6] Creating folders...
if not exist "gymratHD" mkdir "gymratHD"
if not exist "gymratHD\data" mkdir "gymratHD\data"
if not exist "gymratHD\data\workouts" mkdir "gymratHD\data\workouts"
if not exist "gymratHD\data\nutrition" mkdir "gymratHD\data\nutrition"
if not exist "gymratHD\data\progress" mkdir "gymratHD\data\progress"
if not exist "gymratHD\data\exports" mkdir "gymratHD\data\exports"

copy /Y "gymratHD.py" "gymratHD\"
copy /Y "food_database.json" "gymratHD\"
if exist "create_logo.py" copy /Y "create_logo.py" "gymratHD\"
if exist "README.md" copy /Y "README.md" "gymratHD\"
if exist "LICENSE.md" copy /Y "LICENSE.md" "gymratHD\"

echo [OK] Folders and files created
echo.

:: Step 4: Install packages
echo [STEP 4/6] Installing Python packages...
echo This might take a few minutes...

python -m pip install customtkinter --quiet
if %errorlevel% neq 0 (
    echo [WARNING] CustomTkinter install failed, trying without --quiet
    python -m pip install customtkinter
)

python -m pip install pillow pandas matplotlib numpy --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Some packages failed, trying without --quiet
    python -m pip install pillow pandas matplotlib numpy
)

echo [OK] Python packages installed
echo.

:: Step 5: Create launcher
echo [STEP 5/6] Creating launcher...
echo @echo off > "gymratHD\START_GYMRATHD.bat"
echo title gymratHD >> "gymratHD\START_GYMRATHD.bat"
echo cd /d "%%~dp0" >> "gymratHD\START_GYMRATHD.bat"
echo echo Starting gymratHD... >> "gymratHD\START_GYMRATHD.bat"
echo echo github.com/barebonesjones >> "gymratHD\START_GYMRATHD.bat"
echo python gymratHD.py >> "gymratHD\START_GYMRATHD.bat"
echo pause >> "gymratHD\START_GYMRATHD.bat"

echo [OK] Launcher created
echo.

:: Step 6: Create logo (optional)
echo [STEP 6/6] Creating logo...
cd "gymratHD"
if exist "create_logo.py" (
    python create_logo.py
    if %errorlevel% neq 0 (
        echo [WARNING] Logo creation failed but continuing...
    ) else (
        echo [OK] Logo created successfully
    )
) else (
    echo [SKIP] No logo script found
)
cd ..
echo.

:: Create desktop shortcut (simple version)
echo [BONUS] Creating desktop shortcut...
set "DESKTOP=%USERPROFILE%\Desktop"
set "GYMRATHD_DIR=%CD%\gymratHD"

echo Set oWS = WScript.CreateObject("WScript.Shell") > shortcut.vbs
echo sLinkFile = "%DESKTOP%\gymratHD.lnk" >> shortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> shortcut.vbs
echo oLink.TargetPath = "%GYMRATHD_DIR%\START_GYMRATHD.bat" >> shortcut.vbs
echo oLink.WorkingDirectory = "%GYMRATHD_DIR%" >> shortcut.vbs
echo oLink.Description = "gymratHD - The Ultimate Mike Mentzer Tracker" >> shortcut.vbs
echo oLink.Save >> shortcut.vbs

cscript shortcut.vbs //nologo
del shortcut.vbs

echo ================================================================
echo                    INSTALLATION COMPLETE!
echo ================================================================
echo.
echo SUCCESS! gymratHD is installed and ready!
echo.
echo Location: %CD%\gymratHD
echo Desktop Shortcut: gymratHD.lnk
echo.
echo TO START GYMRATHD:
echo   1. Double-click desktop shortcut: gymratHD.lnk
echo   2. Or run: START_GYMRATHD.bat (from gymratHD folder)
echo.
echo FEATURES READY:
echo   Mike Mentzer Heavy Duty protocols
echo   60/25/15 nutrition ratios
echo   Multiple training goals (Strength/Hypertrophy/Power/Endurance)
echo   Comprehensive food database
echo   Real progress tracking
echo   Privacy-first data storage
echo.
echo Created by: github.com/barebonesjones
echo "Recovery is when growth occurs." - Mike Mentzer
echo.
echo Starting gymratHD now...
echo ================================================================
echo.

:: Launch the app
cd "gymratHD"
python gymratHD.py

echo.
echo Thank you for using gymratHD!
echo github.com/barebonesjones
echo.
pause