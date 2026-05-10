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

    MODEL = "gemini-2.5-flash"

    PROMPT = """당신은 세계 최고의 수학 교육용 그래프 분석 전문가입니다. 이미지에서 수학 그래프를 완벽하게 재구성할 수 있도록 정밀한 JSON 데이터를 생성하십시오.

[분석 핵심 원칙 - Zero-Defect]
1. 곡선(Curves)의 미학:
   - 곡선은 절대로 각지면 안 됩니다. 곡률이 큰 구간(예: 굴곡진 부위, 극점 근처)은 좌표를 극도로 촘촘하게(최소 0.05 단위 간격) 추출하십시오.
   - 곡선이 축과 만나는 지점(절편), 함숫값이 불연속인 지점을 수학적으로 정확하게 파악하십시오.
2. 기하학적 정밀도:
   - 원점(O), 축 라벨(x, y), 좌표값(a, L) 등의 위치를 이미지와 1:1로 일치시키십시오.
   - 보조선(Dashed Lines)은 함숫값의 대응 관계를 명확히 보여주어야 합니다.
3. 화살표(Arrows)와 흐름:
   - 극한(Limit)의 흐름을 나타내는 화살표를 빠짐없이 추출하십시오. 
   - 특히 곡선을 따라가는 화살표(`is_curved`: true)는 곡선상의 점들을 정확히 따라가는 15개 이상의 좌표 리스트를 포함해야 합니다.
4. 라벨 배치:
   - 라벨은 텍스트 내용뿐만 아니라 위치(`pos`)가 매우 중요합니다. 그래프 선이나 점과 겹치지 않도록 미세 조정된 좌표를 제공하십시오.

[출력 JSON 구조]
[
  {
    "chart_id": 1,
    "axes": {
      "x_range": [min, max],
      "y_range": [min, max],
      "origin_label": "O", "x_label": "x", "y_label": "y"
    },
    "curves": [
      {
        "points": [[x1,y1],[x2,y2],...], // 곡선을 완벽히 묘사하는 100~200개 점 (초정밀)
        "label": "y=f(x)", "label_pos": [lx, ly], "style": "solid", "width": 2.5
      }
    ],
    "arrows": [
      {
        "from": [x,y], "to": [x,y],
        "is_curved": true/false,
        "points": [[x1,y1],[x2,y2],...], // 곡선형 화살표일 경우 경로 점들
        "label": ""
      }
    ],
    "points": [{"x": x, "y": y, "type": "hollow/filled", "color": "#FFFFFF"}],
    "dashed_lines": [{"type": "horizontal/vertical", "val": v, "start": s, "end": e}],
    "labels": [{"text": "f(a)", "pos": [x, y]}]
  }
]"""

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
