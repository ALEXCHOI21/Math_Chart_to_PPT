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
        사용자가 이미지 내에서 **회색(또는 검은색) 펜으로 동그라미 친 그래프 영역**만 집중적으로 분석하여 고화질 투명 PNG로 재현하기 위한 정밀 데이터를 추출해주세요.
        출력은 반드시 유효한 JSON 형식이어야 하며, 다른 설명은 생략하세요.

        분석 원칙:
        1. **동그라미 영역 집중**: 페이지 전체가 아닌, 원형으로 표시된 그래프 본체만 분석합니다. (이미지에 여러 개가 있다면 리스트 형태로 반환)
        2. **미학적 정밀도**: 축의 화살표 위치, 원점 'O', 축 라벨 'x', 'y'의 정확한 상대적 위치를 파악하세요.
        3. **수식 렌더링**: 그래프에 포함된 모든 수식(예: y=f(x), lim f(x)=L 등)을 완벽한 LaTeX 형식으로 추출하세요.
        4. **곡선 재현**: 곡선의 형태를 완벽하게 재현할 수 있도록 샘플 포인트를 충분히(20개 이상) 추출하세요.

        JSON 구조:
        [
          {
            "chart_id": 1,
            "axes": {
              "x_range": [min, max], "y_range": [min, max],
              "origin_label": "O", "x_label": "x", "y_label": "y",
              "has_arrows": true
            },
            "curves": [
              {
                "points": [[x1, y1], ...],
                "label": "y=f(x)", "is_latex": true,
                "style": "solid", "color": "black", "width": 2
              }
            ],
            "points": [
              {"x": 1, "y": 2, "type": "hollow", "label": "L", "show_dashed_lines": true}
            ],
            "labels": [
                {"text": "\\lim_{x \to a} f(x) = L", "pos": [x, y], "is_latex": true}
            ]
          }
        ]
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
