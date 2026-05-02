// Play.cpp
#include "Play.h"

void Play::Draw(HDC hdc, RECT rc) {
    Graphics graphics(hdc);
    Image image(L"papers\\배경.png");  // ← 배경 이미지
    graphics.DrawImage(&image, (int)rc.left, (int)rc.top, (int)rc.right, (int)rc.bottom);
}