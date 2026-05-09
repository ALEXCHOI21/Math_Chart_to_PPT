import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── .env 가장 먼저 로드 ────────────────────────────────────────
ROOT_PATH = Path(__file__).parent.parent
load_dotenv(ROOT_PATH / ".env")

# ── Internal_Library 경로 추가 (선택적) ───────────────────────
INTERNAL_LIB_PATH = r"D:\CDR_SynologyDrive\10_업무\Internal_Library"
if INTERNAL_LIB_PATH not in sys.path:
    sys.path.append(INTERNAL_LIB_PATH)

# ── API 키 로드 ────────────────────────────────────────────────
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError("❌ GOOGLE_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")

# ── 신규 google-genai SDK 사용 ─────────────────────────────────
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)


class GraphAnalyzer:
    """
    수학 그래프 이미지 1장 → 정밀 JSON 데이터 추출.
    흰색 투명 PNG 재현용 (극한, 점선, 라벨, 화살표 포함).
    """

    MODEL = "gemini-2.5-flash"

    PROMPT = """당신은 수학 교재의 그래프를 분석하는 전문가입니다.
이미지 속 수학 그래프를 분석하여 matplotlib으로 완벽하게 재현할 수 있는 JSON 데이터를 반환하세요.
반드시 JSON 배열만 출력하세요. 설명, 주석, 마크다운 없이 순수 JSON만 출력합니다.

[분석 체크리스트]
1. 축(axis): x축·y축의 범위, 원점 O 위치, 화살표 방향
2. 곡선(curve): S자·포물선·직선 등 형태를 정확히 파악하고, 좌표 샘플 30개 이상 추출
3. 특수점(point): hollow(빈 원) / filled(채운 원) 구분, 좌표 정확히
4. 점선(dashed): 수평·수직 점선의 시작/끝 좌표
5. 라벨(label): L, a, O, x, y 등 모든 텍스트와 위치
6. 극한 화살표: x→a 방향 화살표가 있으면 방향과 위치 모두 포함
7. 수식: LaTeX 형식으로 정확히 추출

[출력 JSON 구조]
[
  {
    "chart_id": 1,
    "axes": {
      "x_range": [-1, 5],
      "y_range": [-1, 4],
      "origin_label": "O",
      "x_label": "x",
      "y_label": "y",
      "has_arrows": true
    },
    "curves": [
      {
        "points": [[x1,y1],[x2,y2],...],
        "label": "y=f(x)",
        "label_pos": [x, y],
        "is_latex": false,
        "style": "solid",
        "width": 2.5
      }
    ],
    "dashed_lines": [
      {"type": "horizontal", "y": 2.1, "x_start": 0, "x_end": 3.2},
      {"type": "vertical",   "x": 3.2, "y_start": 0, "y_end": 2.1}
    ],
    "points": [
      {"x": 3.2, "y": 2.1, "type": "hollow", "label": "", "show_dashed": true}
    ],
    "axis_labels": [
      {"text": "L", "pos": [-0.3, 2.1], "is_latex": false},
      {"text": "a", "pos": [3.2, -0.3], "is_latex": false}
    ],
    "arrows": [
      {"from": [1.5, 0.05], "to": [3.0, 0.05], "label": ""},
      {"from": [4.5, 0.05], "to": [3.4, 0.05], "label": ""}
    ],
    "labels": [
      {"text": "y=f(x)", "pos": [4.2, 3.5], "is_latex": false}
    ]
  }
]"""

    async def analyze(self, image_path: str) -> list:
        """이미지 경로를 받아 그래프 JSON 데이터 리스트를 반환."""
        import asyncio

        with open(image_path, "rb") as f:
            img_bytes = f.read()

        # 확장자로 MIME 타입 결정
        ext = Path(image_path).suffix.lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        def _call():
            response = client.models.generate_content(
                model=self.MODEL,
                contents=[
                    types.Part.from_bytes(data=img_bytes, mime_type=mime),
                    self.PROMPT
                ]
            )
            return response.text

        try:
            text = await asyncio.to_thread(_call)

            # JSON 블록 추출
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())
            if not isinstance(data, list):
                data = [data]
            return data

        except Exception as e:
            print(f"  ⚠️  Gemini 오류: {e}")
            return [{"error": str(e)}]


# ── 단독 실행 테스트 ───────────────────────────────────────────
if __name__ == "__main__":
    import asyncio

    async def test():
        analyzer = GraphAnalyzer()
        result = await analyzer.analyze(
            str(ROOT_PATH / "이미지" / "1.jpg")
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test())
