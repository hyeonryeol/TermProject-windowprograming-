// Play.h
#pragma once
#include <windows.h>
#include <gdiplus.h>
using namespace Gdiplus;

class Play {
public:
    void Draw(HDC hdc, RECT rc);  // ← 배경 그리기
};