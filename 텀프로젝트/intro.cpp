#include "Intro.h"

bool Intro::NextPage() {
    page++;
    if (page >= 3) return true;  // ← 3장 끝나면 true
    return false;
}

int Intro::GetPage() const { return page; }

void Intro::Draw(HDC hdc, RECT rc) {
    Graphics graphics(hdc);
    graphics.Clear(Color(255, 0, 0, 0));
    int x = rc.right / 4;
    int y = rc.bottom / 4;
    PrivateFontCollection pfc;
    pfc.AddFontFile(L"fonts\\선전체.TTF");
    FontFamily fontFamily;
    int found = 0;
    pfc.GetFamilies(1, &fontFamily, &found);
    Font font(&fontFamily, 36, FontStyleRegular, UnitPixel);
    SolidBrush brush(Color(255, 255, 255, 255));
    switch (page)
    {
    case 0:
    {
        // 1번째 인트로 그리기
        Image imageintro1(L"intro\\intro1.png");
        graphics.DrawImage(&imageintro1, x, y-50, 2*x, 2*y-50);
        PointF p(1 * x + 110, 3 * y );
        graphics.DrawString(L"당신은 노동복권에 당첨되었습니다.", -1, &font, p, &brush);
        break;
    }
    case 1:
    {
        // 2번째 인트로 그리기
        Image imageintro2(L"intro\\Obrinspector.png");
        graphics.DrawImage(&imageintro2, x, y - 50, 2 * x, 2 * y - 50);
        PointF p(1 * x, 3 * y );
        graphics.DrawString(L"오브리스탄 출입국관리소에서 근무할 기회를 얻게되었습니다.", -1, &font, p, &brush);
        break;
    }
    case 2:
        // 3번째 인트로 그리기
        Image imageintro3(L"intro\\Arstotzka.png");
        graphics.DrawImage(&imageintro3, x, y - 50, 2 * x, 2 * y - 50);
        PointF p(1 * x+ 140, 3 * y );
        graphics.DrawString(L"아스토츠카의 영광을 위하여..", -1, &font, p, &brush);
        break;
    }

    // NEXT 텍스트
   
    
    PointF point(2*x - 50, 3*y + 100);
    graphics.DrawString(L"NEXT", -1, &font, point, &brush);
}