#pragma once
#include <windows.h>
#include <gdiplus.h>
using namespace Gdiplus;

class Intro {
public:
    void Draw(HDC hdc, RECT rc);
    bool NextPage();       // ← 다음 페이지로, 끝나면 true 반환
    int GetPage() const;   // ← 현재 페이지 반환
    void Update(float deltaTime);  
   
private:
    int page = 0;          // ← 현재 페이지 (0, 1, 2)
    int charIndex = 0;
    float timer = 0.0f;
    float speed = 0.05f; // 글자 속도 (낮을수록 빠름)

 
};