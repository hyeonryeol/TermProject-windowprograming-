#include <windows.h>
#include <gdiplus.h>
#include "Play.h"
#include "Intro.h"   
enum Scene { INTRO, PLAY };
Scene currentScene = INTRO;
#pragma comment(lib, "gdiplus.lib")
using namespace Gdiplus;
Intro intro;  // ← 전역으로 선언 (WndProc 위에)
Play play;
// 윈도우 프로시저 선언
LRESULT CALLBACK WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

// 클래스 이름 / 창 제목
const wchar_t CLASS_NAME[] = L"MyWindowClass";
const wchar_t WINDOW_TITLE[] = L"Win32 Basic Template";


// 프로그램 시작점
int WINAPI wWinMain(HINSTANCE hInstance, HINSTANCE, PWSTR, int nCmdShow)
{
    GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
    // 1) 윈도우 클래스 등록
    WNDCLASSEXW wc = {};
    wc.cbSize = sizeof(wc);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hIcon = LoadIcon(nullptr, IDI_APPLICATION);
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW + 0);
    wc.lpszClassName = CLASS_NAME;
    wc.hIconSm = LoadIcon(nullptr, IDI_APPLICATION);

    RegisterClassExW(&wc);

    // 2) 윈도우 생성
    HWND hWnd = CreateWindowExW(
        0,
        CLASS_NAME,
        WINDOW_TITLE,
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT, CW_USEDEFAULT, 1368, 768,
       
        nullptr, nullptr, hInstance, nullptr
    );

    if (!hWnd) return 0;

    // 3) 창 표시
    ShowWindow(hWnd, nCmdShow);
    UpdateWindow(hWnd);

    // 4) 메시지 루프
    MSG msg = {};
    while (GetMessage(&msg, nullptr, 0, 0))
    {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }
    GdiplusShutdown(gdiplusToken);
    return (int)msg.wParam;
}

// 윈도우 메시지 처리 함수
LRESULT CALLBACK WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    switch (msg)
    {
    case WM_KEYDOWN:
    {
        return 0;
    }
    case WM_LBUTTONDOWN:  // ← 마우스 왼쪽 클릭
    {
        int x = LOWORD(lParam);  // ← 클릭한 X 좌표
        int y = HIWORD(lParam);  // ← 클릭한 Y 좌표
       
        // 여기에 클릭 처리 코드 작성
        if (currentScene == INTRO)
        {
            if (x >= 634 && x <= 734 && y >= 656 && y <= 716)
            {
                bool isEnd = intro.NextPage();
                if (isEnd) currentScene = PLAY;
                InvalidateRect(hWnd, nullptr, TRUE);
            }
        }
        return 0;
    }
    case WM_PAINT:
    {
        PAINTSTRUCT ps;
        HDC hdc = BeginPaint(hWnd, &ps);
        RECT rc;
        GetClientRect(hWnd, &rc);
        
        if (currentScene == INTRO)
            intro.Draw(hdc, rc);
        else if (currentScene == PLAY)
        {
            play.Draw(hdc, rc);
        }
       

        EndPaint(hWnd, &ps);
        return 0;
    }

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }

    return DefWindowProc(hWnd, msg, wParam, lParam);
}