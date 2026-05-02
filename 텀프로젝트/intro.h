#pragma once
#include <windows.h>
#include <gdiplus.h>
using namespace Gdiplus;

class Intro {
public:
    void Draw(HDC hdc, RECT rc);
    bool NextPage();       // ← 다음 페이지로, 끝나면 true 반환
    int GetPage() const;   // ← 현재 페이지 반환

private:
    int page = 0;          // ← 현재 페이지 (0, 1, 2)
};