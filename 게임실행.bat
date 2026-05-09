@echo off
chdir /d "%~dp0"

echo Ursina 설치 확인 중...
python -c "import ursina" 2>nul
if %errorlevel% neq 0 (
    echo Ursina 설치 중...
    pip install ursina -q
)

echo.
echo Iron Crawler 3D 시작!
python main.py
if %errorlevel% neq 0 (
    echo.
    echo 오류가 발생했습니다. 위 메시지를 확인하세요.
    pause
)
