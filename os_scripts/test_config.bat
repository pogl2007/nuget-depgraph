@echo off
cd /d "%~dp0.."
set REPO=https://api.nuget.org/v3-flatcontainer/

echo ===== 1. All parameters are correct =====
python src\main.py --package Serilog --repo %REPO% --version 3.1.1 --max-depth 5
echo exit code: %ERRORLEVEL%

echo ===== 2. Test mode with a repository file =====
python src\main.py --package A --repo test_repos\simple.txt --test-mode --version 1.0
echo exit code: %ERRORLEVEL%

echo ===== 3. Bad package name =====
python src\main.py --package "bad name" --repo %REPO% --version 1.0

echo ===== 4. Bad repository URL =====
python src\main.py --package Serilog --repo ftp://example.com --version 1.0

echo ===== 5. Test repository file not found =====
python src\main.py --package A --repo test_repos\nope.txt --test-mode --version 1.0

echo ===== 6. Bad version =====
python src\main.py --package Serilog --repo %REPO% --version abc

echo ===== 7. Depth less than 1 =====
python src\main.py --package Serilog --repo %REPO% --version 1.0 --max-depth 0

echo ===== 8. Depth is not a number =====
python src\main.py --package Serilog --repo %REPO% --version 1.0 --max-depth abc

echo ===== 9. Several errors at once =====
python src\main.py --package "" --repo x --version 1 --max-depth -2
echo exit code: %ERRORLEVEL%

echo ===== 10. Required parameter is missing =====
python src\main.py --package Serilog
echo exit code: %ERRORLEVEL%
