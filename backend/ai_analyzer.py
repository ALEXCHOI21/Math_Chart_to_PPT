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
    흰색 투명 PNG 재현용 (극한, 점선, 라벨, 화살표 포함).
    """

    MODEL = "gemini-2.5-pro"

    PROMPT = """당신은 전 세계 수학 교재를 만드는 수학 그래프 디지털화의 최고 전문가입니다.
이미지에서 그래프의 모든 기하학적 요소와 수식을 한 치의 오차 없이 정밀한 JSON 데이터로 추출하십시오.

[Perfect Clone v2 - 핵심 추출 원칙]

1. 곡선(curves) - 최고 정밀도 추출:
   - 곡선 하나당 최소 60개 이상의 점 좌표를 추출하십시오.
   - S자형 곡선(변곡점 포함): 변곡점 전후 구간에 좌표를 15개 이상 집중 배치하십시오.
     예) 아래로 내려갔다가 변곡점을 지나 위로 올라가는 형태라면,
     변곡점 직전/직후에 x 간격 0.1 이하로 좌표를 빽빽하게 배치.
   - 빈 원(Hollow circle)이 있어도 곡선을 끊지 말고 하나의 연속 점 집합으로 추출.
   - 곡선이 화면 밖으로 나가면 그 방향을 유지하며 x_range/y_range 끝까지 추적.

2. 화살표(arrows) - 수렴 화살표 완벽 감지:
   - x축 위의 수렴 화살표(→ ←) 쌍을 반드시 2개의 별개 항목으로 표현:
     좌측: {"from": [x_left, 0], "to": [a-0.15, 0], "is_curved": false, "color": "#FFFFFF"}
     우측: {"from": [x_right, 0], "to": [a+0.15, 0], "is_curved": false, "color": "#FFFFFF"}
   - from은 화살표 꼬리, to는 화살표 머리(끝점).
   - 곡선 위의 방향 화살표도 누락 없이 추출.

3. 라벨(labels) - 텍스트 순수 추출:
   - 라벨 text 필드에 절대 $ 기호를 포함하지 마십시오. 렌더러가 자동 처리합니다.
     올바른 예: "text": "y=f(x)",  "text": "L",  "text": "a",  "text": "O"
     잘못된 예: "text": "$y=f(x)$",  "text": "$L$"
   - 위치(pos) 기준:
     a 라벨: x축 바로 아래, pos = [a_value, -0.3]
     L 라벨: y축 바로 왼쪽, pos = [-0.4, L_value]
     y=f(x) 라벨: 곡선 상단 오른쪽, 실제 위치와 1:1 대응

4. 기하학적 디테일:
   - 빈 원(hollow): 정확한 좌표에 {"x": a, "y": L, "type": "hollow", "color": "#FFFFFF"}
   - 점선: vertical은 x=a에서 y=0~L, horizontal은 y=L에서 x=0~a
   - 원점 O, 축 라벨 x/y 모두 labels에 포함

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
        "points": [[x1,y1], [x2,y2], ..., [x60,y60]],
        "style": "solid",
        "color": "#FFFFFF",
        "width": 3.0
      }
    ],
    "arrows": [
      {"from": [x_left, 0], "to": [a_minus_offset, 0], "is_curved": false, "color": "#FFFFFF"},
      {"from": [x_right, 0], "to": [a_plus_offset, 0], "is_curved": false, "color": "#FFFFFF"}
    ],
    "points": [
      {"x": a, "y": L, "type": "hollow", "color": "#FFFFFF"}
    ],
    "dashed_lines": [
      {"type": "vertical", "val": a, "start": 0, "end": L},
      {"type": "horizontal", "val": L, "start": 0, "end": a}
    ],
    "labels": [
      {"text": "y=f(x)", "pos": [x_pos, y_pos]},
      {"text": "a", "pos": [a, -0.3]},
      {"text": "L", "pos": [-0.4, L]},
      {"text": "O", "pos": [-0.3, -0.3]}
    ]
  }
]

완벽한 복제가 목표입니다. 수학 논문에 실릴 수준의 정교함을 갖추십시오."""

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
            # 1순위: ```json ... ``` 코드 블록
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            # 2순위: ``` ... ``` 코드 블록
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            # $$ 등 수식 래퍼 제거 (AI가 실수로 붙이는 경우)
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
