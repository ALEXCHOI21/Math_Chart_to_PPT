import os
import json
import sys
from pathlib import Path
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv

# Internal_Library 경로 추가 및 SecretVault 연동
INTERNAL_LIB_PATH = r"D:\CDR_SynologyDrive\10_업무\Internal_Library"
if INTERNAL_LIB_PATH not in sys.path:
    sys.path.append(INTERNAL_LIB_PATH)

try:
    from backend.security.vault import SecretVault
    vault = SecretVault()
    api_key = vault.google_api_key
except ImportError:
    # 폴백: 로컬 .env 또는 환경 변수
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

# Gemini API 설정
if api_key:
    genai.configure(api_key=api_key)
else:
    print("⚠️ Warning: GOOGLE_API_KEY not found in Vault or Environment.")

class GraphAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def analyze(self, image_path):
        """이미지를 분석하여 그래프 데이터를 JSON으로 반환합니다."""
        img = Image.open(image_path)
        
        prompt = """
        이 이미지에 있는 수학 그래프를 분석하여 PPT 개체로 재구성하기 위한 상세 데이터를 추출해주세요.
        출력은 반드시 유효한 JSON 형식이어야 하며, 다른 텍스트는 포함하지 마세요.

        분석 항목:
        1. axes: x축과 y축의 범위, 원점 위치, 축의 화살표 유무.
        2. grid: 격자선 유무 및 간격.
        3. curves: 그래프 선의 종류(직선, 곡선, 점선 등)와 주요 좌표점 리스트(곡선의 경우 최소 10개 이상의 샘플 포인트).
        4. points: 강조된 점(예: 극한값, 교점)의 좌표와 채워짐 여부(solid/hollow).
        5. labels: 축 이름, 눈금 숫자, 함수 수식(LaTeX) 및 그 위치.

        JSON 구조 예시:
        {
          "axes": {
            "x_min": -5, "x_max": 5, "y_min": -5, "y_max": 5,
            "origin": [0, 0], "arrows": true
          },
          "curves": [
            {
              "type": "bezier",
              "points": [[x1, y1], [x2, y2], ...],
              "equation": "y=f(x)",
              "style": "solid"
            }
          ],
          "points": [
            {"coord": [1, 2], "type": "hollow", "label": "L"}
          ],
          "labels": [
            {"text": "x", "pos": [5.2, 0]},
            {"text": "y", "pos": [0, 5.2]}
          ]
        }
        """

        try:
            import asyncio
            def call_api():
                return self.model.generate_content([prompt, img])
            response = await asyncio.to_thread(call_api)
            text = response.text
            
            # JSON 텍스트 추출
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            data = json.loads(text.strip())
            return data
        except Exception as e:
            print(f"Gemini Analysis Error: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    import asyncio
    async def test():
        analyzer = GraphAnalyzer()
        res = await analyzer.analyze(r"D:\CDR_SynologyDrive\00_AI_AGENT\01_EDU\도구\수학 그래프 PPT 변환\이미지\1.jpg")
        print(json.dumps(res, indent=2))
    asyncio.run(test())
