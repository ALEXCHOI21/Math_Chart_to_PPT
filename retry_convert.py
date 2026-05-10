import os
import json
import asyncio
import sys
from pathlib import Path

# backend 경로 추가
CURRENT_DIR = Path(os.getcwd())
sys.path.append(str(CURRENT_DIR / 'backend'))

from ai_analyzer import GraphAnalyzer
from converter import PPTConverter

async def retry_single(img_name):
    IMAGE_DIR = CURRENT_DIR / "이미지"
    RESULTS_DIR = CURRENT_DIR / "results"
    
    analyzer = GraphAnalyzer()
    converter = PPTConverter()
    
    img_path = str(IMAGE_DIR / img_name)
    print(f"--- Retrying {img_name} ---")
    
    # 1. AI 분석
    analysis_json = await analyzer.analyze(img_path)
    
    if "error" in analysis_json[0]:
        print(f"Retry failed again: {analysis_json[0]['error']}")
        return

    base_name = os.path.splitext(img_name)[0]
    pptx_path = str(RESULTS_DIR / f"{base_name}_result.pptx")
    png_path = str(RESULTS_DIR / f"{base_name}_result.png")
    json_path = str(RESULTS_DIR / f"{base_name}_result.json")
    
    converter.create_ppt(analysis_json, pptx_path)
    converter.export_as_png(analysis_json, png_path)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(analysis_json, f, ensure_ascii=False, indent=2)
    print(f"Retry success: {img_name}")

if __name__ == "__main__":
    asyncio.run(retry_single("4.jpg"))
