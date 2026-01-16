@echo off
echo ========================================
echo King-Phisher Project Cleanup
echo ========================================
echo.
echo This will remove 20 unnecessary files:
echo - 4 duplicate/obsolete backend files
echo - 9 misplaced template files
echo - 7 redundant documentation files
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Starting cleanup...
echo.

REM Backend root duplicates
echo [1/4] Cleaning backend root...
if exist backend\dashboard.html (
    del backend\dashboard.html
    echo   ✓ Removed backend\dashboard.html
)
if exist backend\manifest.json (
    del backend\manifest.json
    echo   ✓ Removed backend\manifest.json
)
if exist backend\server.py (
    del backend\server.py
    echo   ✓ Removed backend\server.py
)
if exist backend\users.bak (
    del backend\users.bak
    echo   ✓ Removed backend\users.bak
)

REM Misplaced template files
echo.
echo [2/4] Cleaning misplaced template files...
if exist backend\templates\auth.js (
    del backend\templates\auth.js
    echo   ✓ Removed backend\templates\auth.js
)
if exist backend\templates\background.js (
    del backend\templates\background.js
    echo   ✓ Removed backend\templates\background.js
)
if exist backend\templates\content.js (
    del backend\templates\content.js
    echo   ✓ Removed backend\templates\content.js
)
if exist backend\templates\manifest.json (
    del backend\templates\manifest.json
    echo   ✓ Removed backend\templates\manifest.json
)
if exist backend\templates\popup.html (
    del backend\templates\popup.html
    echo   ✓ Removed backend\templates\popup.html
)

REM Obsolete templates
echo.
echo [3/4] Cleaning obsolete templates...
if exist backend\templates\dashboard.html (
    del backend\templates\dashboard.html
    echo   ✓ Removed backend\templates\dashboard.html
)
if exist backend\templates\scan.html (
    del backend\templates\scan.html
    echo   ✓ Removed backend\templates\scan.html
)
if exist backend\templates\profile.html (
    del backend\templates\profile.html
    echo   ✓ Removed backend\templates\profile.html
)
if exist backend\templates\settings.html (
    del backend\templates\settings.html
    echo   ✓ Removed backend\templates\settings.html
)

REM Redundant documentation
echo.
echo [4/4] Cleaning redundant documentation...
if exist PHASE_6_PROGRESS.md (
    del PHASE_6_PROGRESS.md
    echo   ✓ Removed PHASE_6_PROGRESS.md
)
if exist PHASE_1_2_COMPLETE.md (
    del PHASE_1_2_COMPLETE.md
    echo   ✓ Removed PHASE_1_2_COMPLETE.md
)
if exist PHASE_4_COMPLETE.md (
    del PHASE_4_COMPLETE.md
    echo   ✓ Removed PHASE_4_COMPLETE.md
)
if exist PHASE_5_COMPLETE.md (
    del PHASE_5_COMPLETE.md
    echo   ✓ Removed PHASE_5_COMPLETE.md
)
if exist QUICK_START_IMPROVEMENTS.md (
    del QUICK_START_IMPROVEMENTS.md
    echo   ✓ Removed QUICK_START_IMPROVEMENTS.md
)
if exist IMPLEMENTATION_PROGRESS.md (
    del IMPLEMENTATION_PROGRESS.md
    echo   ✓ Removed IMPLEMENTATION_PROGRESS.md
)
if exist FINAL_SUMMARY.md (
    del FINAL_SUMMARY.md
    echo   ✓ Removed FINAL_SUMMARY.md
)

echo.
echo ========================================
echo ✓ Cleanup Complete!
echo ========================================
echo.
echo Removed 20 unnecessary files.
echo.
echo Kept essential files:
echo   - app.py, model.py, integrations.py, threat_intel.py
echo   - Enhanced templates (dashboard_enhanced.html, scan_enhanced.html, bulk_scan.html)
echo   - Extension files
echo   - Tests
echo   - README.md, ALL_PHASES_COMPLETE.md, PHASE_6_COMPLETE.md
echo.
echo Your project is now clean and organized! 🧹
echo.
pause
