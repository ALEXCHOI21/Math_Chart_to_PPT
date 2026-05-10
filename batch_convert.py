import os
import json
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# backend 경로 추가
CURRENT_DIR = Path(os.getcwd())
sys.path.append(str(CURRENT_DIR / 'backend'))

from ai_analyzer import GraphAnalyzer
from converter import PPTConverter

# 설정
IMAGE_DIR = CURRENT_DIR / "이미지"
RESULTS_DIR = CURRENT_DIR / "results"
FRONTEND_DATA = CURRENT_DIR / "frontend" / "results.json"

async def batch_process():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
        print(f"Created directory: {RESULTS_DIR}")

    analyzer = GraphAnalyzer()
    converter = PPTConverter()
    
    results_list = []
    
    images = sorted([f for f in os.listdir(IMAGE_DIR) if f.endswith(('.jpg', '.png', '.jpeg'))])
    
    for img_name in images:
        img_path = str(IMAGE_DIR / img_name)
        print(f"--- Processing {img_name} ---")
        
        try:
            # 1. AI 분석 (Async 호출)
            print("Analyzing with Gemini...")
            analysis_json = await analyzer.analyze(img_path)
            
            # 2. 파일명 생성
            base_name = os.path.splitext(img_name)[0]
            pptx_filename = f"{base_name}_result.pptx"
            png_filename = f"{base_name}_result.png"
            json_filename = f"{base_name}_result.json"
            
            pptx_path = str(RESULTS_DIR / pptx_filename)
            png_path = str(RESULTS_DIR / png_filename)
            json_path = str(RESULTS_DIR / json_filename)
            
            # 3. PPT 및 PNG 생성
            print("Generating PPTX and PNG...")
            converter.create_ppt(analysis_json, pptx_path)
            converter.export_as_png(analysis_json, png_path)
            
            # 4. JSON 저장 (디버깅용)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(analysis_json, f, ensure_ascii=False, indent=2)
            
            # 5. 결과 리스트 추가 (프론트엔드용 경로)
            results_list.append({
                "original": img_name,
                "result_png": f"results/{png_filename}",
                "result_pptx": f"results/{pptx_filename}",
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            print(f"Success: {img_name}")
            
        except Exception as e:
            print(f"Error processing {img_name}: {str(e)}")

    # 6. 프론트엔드용 데이터 파일 저장
    with open(FRONTEND_DATA, 'w', encoding='utf-8') as f:
        json.dump(results_list, f, ensure_ascii=False, indent=2)
    print(f"Frontend data saved to {FRONTEND_DATA}")

if __name__ == "__main__":
    asyncio.run(batch_process())
