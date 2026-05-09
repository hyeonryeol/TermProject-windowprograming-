@echo off
chdir /d "%~dp0"
echo pygame 설치 확인 중...
pip install pygame -q
echo.
echo Iron Crawler 시작!
python main.py
if %errorlevel% neq 0 (
    echo.
    echo 오류가 발생했습니다. 위 메시지를 확인하세요.
    pause
)
