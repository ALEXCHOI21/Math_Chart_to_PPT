import os
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
ROOT_PATH = Path(r"D:\CDR_SynologyDrive\00_AI_AGENT\01_EDU\도구\수학 그래프 PPT 변환")
sys.path.append(str(ROOT_PATH))

from backend.ai_analyzer import GraphAnalyzer
from backend.converter import PPTConverter
from backend.png_generator import PNGGenerator

async def process_images():
    image_dir = ROOT_PATH / "이미지"
    output_dir = ROOT_PATH / "output"
    
    analyzer = GraphAnalyzer()
    converter = PPTConverter()
    png_gen = PNGGenerator(str(output_dir))
    
    if not output_dir.exists():
        output_dir.mkdir()
        
    images = ["1.jpg", "2.jpg", "3.jpg"]
    
    for img_name in images:
        img_path = image_dir / img_name
        if not img_path.exists():
            print(f"Skipping {img_name}: File not found.")
            continue
            
        print(f"Analyzing {img_name}...")
        try:
            # AI 분석 수행
            data = await analyzer.analyze(str(img_path))
            
            if "error" in data:
                print(f"Error analyzing {img_name}: {data['error']}")
                continue
                
            # PPT 변환 수행
            output_name = img_name.replace(".jpg", ".pptx")
            output_path = output_dir / output_name
            
            print(f"Converting to PPT: {output_name}...")
            converter.create_ppt(data, str(output_path))
            
            # 투명 PNG 생성 수행 (추가요청)
            png_name = img_name.replace(".jpg", ".png")
            print(f"Generating Transparent PNG: {png_name}...")
            png_gen.generate_transparent_png(data, png_name)
            
            print(f"Successfully created results for {img_name}")
            
        except Exception as e:
            print(f"Failed to process {img_name}: {e}")

if __name__ == "__main__":
    asyncio.run(process_images())
