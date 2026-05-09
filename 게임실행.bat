@echo off
chdir /d "%~dp0"

echo pygame 설치 확인 중...
python -c "import pygame" 2>nul
if %errorlevel% neq 0 (
    echo pygame 없음. pygame-ce 설치 중...
    pip install pygame-ce -q
    if %errorlevel% neq 0 (
        echo pygame-ce 실패. 다른 방법 시도 중...
        pip install pygame --pre -q
    )
)

echo.
echo Iron Crawler 시작!
python main.py
if %errorlevel% neq 0 (
    echo.
    echo 오류가 발생했습니다. 위 메시지를 확인하세요.
    pause
)
