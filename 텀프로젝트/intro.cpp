#include "Intro.h"
#include <string>  
bool Intro::NextPage() {
    page++;
    // ↓ 이 두 줄 추가 (페이지 넘길 때 애니메이션 리셋)
    charIndex = 0;
    timer = 0.0f;
    if (page >= 3) return true;
    return false;
}

int Intro::GetPage() const { return page; }
// Draw() 함수 위에 새로 추가
void Intro::Update(float deltaTime) {
    const wchar_t* texts[] = {
        L"당신은 노동복권에 당첨되었습니다.",
        L"오브리스탄 출입국관리소에서 근무할 기회를 얻게되었습니다.",
        L"아스토츠카의 영광을 위하여.."
    };
    std::wstring fullText = texts[page];

    if (charIndex < (int)fullText.size()) {
        timer += deltaTime;
        if (timer >= speed) {
            charIndex++;
            timer = 0.0f;
        }
    }
}

void Intro::Draw(HDC hdc, RECT rc) {
    Graphics graphics(hdc);
    graphics.Clear(Color(255, 0, 0, 0));
    int x = rc.right / 4;
    int y = rc.bottom / 4;
    PrivateFontCollection pfc;
    pfc.AddFontFile(L"fonts\\sunjeon.TTF");
    FontFamily fontFamily;
    int found = 0;
    pfc.GetFamilies(1, &fontFamily, &found);
    Font font(&fontFamily, 36, FontStyleRegular, UnitPixel);
    SolidBrush brush(Color(255, 255, 255, 255));
    switch (page)
    {
    case 0:
    {
        Image img(L"intro\\intro1.png");
        graphics.DrawImage(&img, x, y - 50, 2 * x, 2 * y - 50);
        PointF p(1 * x + 110, 3 * y);
        std::wstring fullText = L"당신은 노동복권에 당첨되었습니다.";
        std::wstring displayText = fullText.substr(0, charIndex);
        graphics.DrawString(displayText.c_str(), -1, &font, p, &brush);
        break;
    }
    case 1:
    {
        Image img(L"intro\\Obrinspector.png");
        graphics.DrawImage(&img, x, y - 50, 2 * x, 2 * y - 50);
        PointF p(1 * x, 3 * y);
        std::wstring fullText = L"오브리스탄 출입국관리소에서 근무할 기회를 얻게되었습니다.";
        std::wstring displayText = fullText.substr(0, charIndex);
        graphics.DrawString(displayText.c_str(), -1, &font, p, &brush);
        break;
    }
    case 2:
    {
        Image img(L"intro\\Arstotzka.png");
        graphics.DrawImage(&img, x, y - 50, 2 * x, 2 * y - 50);
        PointF p(1 * x + 140, 3 * y);
        std::wstring fullText = L"아스토츠카의 영광을 위하여..";
        std::wstring displayText = fullText.substr(0, charIndex);
        graphics.DrawString(displayText.c_str(), -1, &font, p, &brush);
        break;
    }
    }  // ← switch 닫기

    // NEXT 텍스트
    PointF point(2 * x - 50, 3 * y + 100);
    graphics.DrawString(L"NEXT", -1, &font, point, &brush);
    }
    // NEXT 텍스트


  