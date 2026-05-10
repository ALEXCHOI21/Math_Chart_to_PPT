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
api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("❌ GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다. .env 파일이나 서버 환경변수를 확인하세요.")

import google.generativeai as genai

genai.configure(api_key=api_key)


class GraphAnalyzer:
    """
    수학 그래프 이미지 1장 → 정밀 JSON 데이터 추출.
    흰색 투명 PNG 재현용 (극한, 점선, 라벨, 화살표 포함).
    """

    MODEL = "gemini-2.5-pro"

    PROMPT = """당신은 전 세계 수학 교재를 만드는 '수학 그래프 디지털화'의 정점(Zenith)에 있는 전문가입니다. 
이미지에서 그래프의 모든 기하학적 요소와 수식을 한 치의 오차 없이 정밀한 JSON 데이터로 추출하는 것이 당신의 사명입니다.

[분석 핵심 원칙 - Zero-Defect & Ultra-Precision]
1. 곡선(Curves)의 생명력:
   - 곡선은 절대로 꺾인 선으로 표현되어서는 안 됩니다. 
   - **중요**: 곡선 하나당 최소 20개에서 50개 사이의 점 좌표(`points`)를 추출하십시오. 특히 굴곡이 있는 지점(극대, 극소, 변곡점) 주변은 좌표를 더욱 촘촘하게 배치하십시오.
   - 점이 부족하면 그래프가 직선으로 렌더링되니 반드시 20개 이상의 점을 확보하십시오.

2. 극한 및 흐름 화살표 (Flow Arrows):
   - 이미지에 곡선을 따라 움직이는 작은 화살표(극한의 수렴/발산 표현 등)가 있다면 반드시 `arrows` 항목에 포함하십시오.
   - `is_curved: true`로 설정하고, 화살표의 경로(`points`)를 곡선과 동일하게 촘촘히 묘사하십시오.

3. 텍스트 및 라벨 배치:
   - 모든 수식($y=f(x)$ 등)과 변수($a, L, x, y, O$)를 누락 없이 추출하십시오.
   - 라벨의 위치(`pos`)는 실제 이미지에서 텍스트의 중심점 좌표를 기준으로 하되, 선이나 점과 겹쳐서 가독성이 떨어지지 않도록 미세하게(0.1 단위) 조정하십시오.

4. 기하학적 구성 요소:
   - 빈 원(Hollow circle)과 채워진 원(Filled circle)을 정확히 구분하십시오.
   - 보조 점선(Dashed Lines)의 시작과 끝을 이미지와 일치시키십시오.

[출력 JSON 구조 가이드]
[
  {
    "chart_id": 1,
    "axes": {
      "x_range": [min, max], // 예: [-2, 6]
      "y_range": [min, max], // 예: [-1, 5]
      "origin_label": "O", "x_label": "x", "y_label": "y"
    },
    "curves": [
      {
        "points": [[x1,y1], [x2,y2], ..., [x50,y50]], // 20~50개의 촘촘한 좌표
        "label": "y=f(x)", 
        "label_pos": [x, y], 
        "style": "solid", 
        "color": "#FFFFFF",
        "width": 2.5
      }
    ],
    "arrows": [
      {
        "from": [x1,y1], "to": [x2,y2],
        "is_curved": true,
        "points": [[x,y], ...], // 곡선을 따라가는 화살표의 경로
        "label": ""
      }
    ],
    "points": [
      {"x": a, "y": L, "type": "hollow", "color": "#FFFFFF"}
    ],
    "dashed_lines": [
      {"type": "vertical", "val": a, "start": 0, "end": L},
      {"type": "horizontal", "val": L, "start": 0, "end": a}
    ],
    "labels": [
      {"text": "a", "pos": [a, -0.3]},
      {"text": "L", "pos": [-0.4, L]}
    ]
  }
]
마지막으로, 당신은 전문가로서 수식의 폰트가 깔끔하고 배치가 아름다워야 함을 명심하십시오."""

    async def analyze(self, image_path: str) -> list:
        """이미지 경로를 받아 그래프 JSON 데이터 리스트를 반환."""
        import asyncio

        # 확장자로 MIME 타입 결정
        ext = Path(image_path).suffix.lower()
        mime = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

        with open(image_path, "rb") as f:
            img_data = f.read()

        model = genai.GenerativeModel(self.MODEL)

        def _call():
            response = model.generate_content([
                {"mime_type": mime, "data": img_data},
                self.PROMPT
            ])
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
