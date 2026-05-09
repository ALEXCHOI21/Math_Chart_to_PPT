import os
import json
import sys
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

# ── 경로 설정 ──────────────────────────────────────────────────
INTERNAL_LIB_PATH = r"D:\CDR_SynologyDrive\10_업무\Internal_Library"
if INTERNAL_LIB_PATH not in sys.path:
    sys.path.append(INTERNAL_LIB_PATH)

# ── API 키 로드 ────────────────────────────────────────────────
try:
    from backend.security.vault import SecretVault
    api_key = SecretVault().google_api_key
except ImportError:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY", "AIzaSyCaXIU9NTdcU0QPe7jLsSM0rQF8b4JD6xA")

# ── 신규 google-genai SDK 사용 ─────────────────────────────────
from google import genai
from google.genai import types

client = genai.Client(api_key=api_key)

class GraphAnalyzer:
    """
    이미지 1장 = 수학 그래프 1개를 기준으로 분석.
    흰색 테마 PNG 재현을 위한 정밀 좌표 데이터를 JSON으로 반환.
    """

    MODEL = "gemini-2.5-flash"

    PROMPT = """
이미지 속 수학 그래프를 분석하여 흰색 선 투명 PNG로 재현할 수 있는 정밀 JSON 데이터를 반환하세요.
반드시 JSON 배열만 출력하세요. 다른 설명은 절대 포함하지 마세요.

분석 원칙:
1. 축(x축, y축)의 방향, 화살표 위치, 원점 'O' 위치를 정확히 파악하세요.
2. 곡선의 형태를 완벽히 재현할 수 있도록 좌표 샘플 포인트를 20개 이상 추출하세요.
3. 수식, 라벨(y=f(x) 등)은 LaTeX 형식으로 추출하세요.
4. 점선(dashed line), 특수점(hollow/filled circle)의 위치와 속성을 파악하세요.

출력 JSON 구조 (반드시 이 형식의 배열):
[
  {
    "chart_id": 1,
    "axes": {
      "x_range": [-3, 5],
      "y_range": [-2, 4],
      "origin_label": "O",
      "x_label": "x",
      "y_label": "y",
      "has_arrows": true
    },
    "curves": [
      {
        "points": [[x1,y1],[x2,y2],...],
        "label": "y=f(x)",
        "is_latex": true,
        "style": "solid",
        "width": 2
      }
    ],
    "points": [
      {"x": 1, "y": 2, "type": "hollow", "label": "A", "show_dashed_lines": true}
    ],
    "labels": [
      {"text": "y=f(x)", "pos": [2.5, 3.0], "is_latex": true}
    ]
  }
]
"""

    async def analyze(self, image_path: str) -> list:
        """이미지 경로를 받아 그래프 JSON 데이터 리스트를 반환."""
        import asyncio

        img = Image.open(image_path)

        def _call():
            response = client.models.generate_content(
                model=self.MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=open(image_path, "rb").read(),
                        mime_type="image/jpeg"
                    ),
                    self.PROMPT
                ]
            )
            return response.text

        try:
            text = await asyncio.to_thread(_call)

            # JSON 추출
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
            r"D:\CDR_SynologyDrive\00_AI_AGENT\01_EDU\도구\수학 그래프 PPT 변환\이미지\1.jpg"
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test())
