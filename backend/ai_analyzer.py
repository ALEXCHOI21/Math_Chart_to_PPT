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
    raise RuntimeError("GOOGLE_API_KEY 또는 GEMINI_API_KEY가 설정되지 않았습니다.")

import google.generativeai as genai

genai.configure(api_key=api_key)


class GraphAnalyzer:
    """
    수학 그래프 이미지 1장 -> 정밀 JSON 데이터 추출.
    Perfect Clone v3: 겹쳤을 때 원본과 픽셀 수준으로 일치하는 좌표 추출.
    """

    MODEL = "gemini-2.5-pro"

    PROMPT = """당신은 수학 그래프 디지털화의 최고 전문가입니다.
목표: 이 이미지의 그래프를 재렌더링했을 때, 원본 위에 투명하게 겹쳤을 때 완벽히 일치(Pixel-Perfect Overlay)해야 합니다.

[Perfect Clone v3 - 겹쳤을 때 완전히 일치하는 수준의 정밀도]

STEP 1. 좌표계를 먼저 정확히 확정하십시오
- x_range: 이미지에 보이는 x축의 대략적인 범위 [x_min, x_max]
- y_range: 이미지에 보이는 y축의 대략적인 범위 [y_min, y_max]
- 가장 중요: 원점(O)이 수학 좌표 [0, 0]에 대응되도록 모든 좌표를 보정하십시오.
- 그래프의 특징점(예: a)을 기준으로 다른 좌표들의 비율을 상대적으로 추정하십시오.

STEP 2. 곡선 좌표는 "핵심 랜드마크 5~10개"만 정확하게 추출하십시오. (절대 수십 개를 임의로 지어내지 마십시오!)
- AI는 점을 많이 생성하려 할 때 허구의 수학 함수를 만들어내는(Hallucination) 경향이 있습니다. 이를 방지하기 위해 반드시 눈에 보이는 주요 교차점만 추출하십시오.
- 필수 포함 랜드마크:
  1. 곡선의 시작점
  2. x축과의 교점 (x절편)
  3. y축과의 교점 (y절편) -> 원본을 보고 양수/음수 여부를 절대 틀리지 마십시오!
  4. 변곡점 또는 극값(가장 볼록한/오목한 곳)
  5. 명시적으로 라벨이 표시된 점 (예: x=a 인 점)
  6. 곡선의 끝점
- 추출한 5~10개의 점만 배열로 반환하면, 렌더러가 자동으로 부드러운 스플라인 곡선으로 연결합니다.

STEP 3. 점(Point)의 유형을 반드시 정확히 판별하십시오
[핵심 규칙 - 절대 혼동 금지]
- 속이 완전히 채워진 점(●): "type": "filled"  <- 내부가 흰색/검정으로 꽉 차 있음
- 속이 빈 원(○): "type": "hollow"  <- 내부가 배경색과 같음 (비어 있음)
- 판별 방법: 원의 내부가 배경색이면 hollow, 곡선 색과 같으면 filled.
- 수학적 의미:
  * filled (●): x=a에서 함수값 f(a)가 실제로 존재/정의됨
  * hollow (○): x=a에서 극한값이지만 함수값은 제외 (불연속점)

STEP 4. 화살표를 정확히 추출하십시오
- x축 위의 수렴 화살표(좌우에서 a로 향하는 쌍)는 반드시 2개 별개 항목:
  * 왼쪽 화살표 (→ 방향): from=[x_left, y_ax], to=[a-gap, y_ax]
  * 오른쪽 화살표 (← 방향): from=[x_right, y_ax], to=[a+gap, y_ax]
  * y_ax는 화살표가 위치한 y 좌표값 (보통 0이거나 아주 작은 양수)
- from은 꼬리, to는 머리(화살 끝).

STEP 5. 라벨 위치를 이미지와 정확히 대응시키십시오
- text 필드에 절대 $ 기호를 넣지 마십시오. 렌더러가 자동 처리합니다.
  올바른 예: "y=f(x)", "f(a)", "a", "O"
  잘못된 예: "$y=f(x)$", "$f(a)$"
- 각 라벨의 pos는 수학 좌표로 이미지와 1:1 대응:
  * y=f(x): 곡선 상단 오른쪽 근처의 실제 위치
  * f(a) 또는 L: y축 왼쪽, 수평 점선 높이와 동일한 y 좌표
  * a: x축 바로 아래, 수직 점선 x 좌표와 동일한 x 좌표
  * O: 원점 왼쪽/아래쪽 약간 오프셋

[출력 JSON 형식 - 이 구조를 정확히 따르십시오]
[
  {
    "chart_id": 1,
    "axes": {
      "x_range": [xmin, xmax],
      "y_range": [ymin, ymax],
      "origin_label": "O",
      "x_label": "x",
      "y_label": "y"
    },
    "curves": [
      {
        "points": [[x1,y1], [x2,y2], [x3,y3], [x4,y4], [x5,y5], [x6,y6]],
        "style": "solid",
        "color": "#FFFFFF",
        "width": 3.0
      }
    ],
    "arrows": [
      {"from": [x_left, y_ax], "to": [a_minus_gap, y_ax], "is_curved": false, "color": "#FFFFFF"},
      {"from": [x_right, y_ax], "to": [a_plus_gap, y_ax], "is_curved": false, "color": "#FFFFFF"}
    ],
    "points": [
      {"x": a_val, "y": fa_val, "type": "filled", "color": "#FFFFFF"}
    ],
    "dashed_lines": [
      {"type": "vertical", "val": a_val, "start": 0, "end": fa_val},
      {"type": "horizontal", "val": fa_val, "start": 0, "end": a_val}
    ],
    "labels": [
      {"text": "y=f(x)", "pos": [x_label, y_label]},
      {"text": "f(a)", "pos": [-0.5, fa_val]},
      {"text": "a", "pos": [a_val, -0.3]},
      {"text": "O", "pos": [-0.35, -0.3]}
    ]
  }
]

[출력 전 자가 검증]
1. 모든 라벨 text에 $ 기호가 없는가?
2. 점(point)의 type이 이미지와 정확히 일치하는가? (filled vs hollow)
3. 곡선 points에 x절편과 y절편이 실제 이미지의 음/양 위치와 일치하게 포함되었는가? (특히 y절편 위치 주의!)
4. 수렴 화살표가 2개인가? (방향이 서로 반대인가?)
5. axes의 x_range, y_range가 합리적인가?

완벽한 픽셀 일치(Pixel-Perfect Overlay)가 목표입니다. 겹쳤을 때 두 그래프가 완전히 일치해야 합니다."""

    async def analyze(self, image_path: str) -> list:
        """이미지 경로를 받아 그래프 JSON 데이터 리스트를 반환."""
        import asyncio

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

            # ── JSON 블록 추출 (AI가 다양한 형태로 감쌀 수 있음) ──────────
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            # $$ 등 수식 래퍼 제거
            text = text.strip()
            if text.startswith("$$"):
                text = text[2:]
            if text.endswith("$$"):
                text = text[:-2]
            text = text.strip()

            # [ 또는 { 로 시작하는 순수 JSON 부분만 추출
            start_idx = -1
            for i, ch in enumerate(text):
                if ch in ('[', '{'):
                    start_idx = i
                    break
            if start_idx > 0:
                text = text[start_idx:]

            data = json.loads(text.strip())
            if not isinstance(data, list):
                data = [data]
            return data

        except Exception as e:
            print(f"  Gemini 오류: {e}")
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
