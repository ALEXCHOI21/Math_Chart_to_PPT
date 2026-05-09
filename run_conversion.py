import os
import asyncio
import sys
import json
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
        
    # 이미지 폴더 내의 모든 jpg, png 파일 검색
    images = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    images.sort() # 순서 정렬
    
    for img_name in images:
        img_path = image_dir / img_name
            
        print(f"Analyzing {img_name}...")
        try:
            # AI 분석 수행
            graph_list = await analyzer.analyze(str(img_path))
            
            if not isinstance(graph_list, list):
                graph_list = [graph_list] # 리스트가 아니면 리스트로 감쌈
            
            if "error" in graph_list[0]:
                print(f"Error analyzing {img_name}: {graph_list[0]['error']}")
                continue
                
            # 각 그래프별로 처리
            for i, data in enumerate(graph_list):
                suffix = f"_{i+1}" if len(graph_list) > 1 else ""
                
                # PPT 변환 수행
                output_name = img_name.replace(".jpg", f"{suffix}.pptx")
                output_path = output_dir / output_name
                print(f"Converting to PPT: {output_name}...")
                converter.create_ppt(data, str(output_path))
                
                # 투명 PNG 생성 수행
                png_name = img_name.replace(".jpg", f"{suffix}.png")
                print(f"Generating Transparent PNG: {png_name}...")
                png_gen.generate_transparent_png(data, png_name)
                
            print(f"Successfully created {len(graph_list)} results for {img_name}")
            
            print(f"Successfully created results for {img_name}")
            
        except Exception as e:
            print(f"Failed to process {img_name}: {e}")

    # 결과 메타데이터 생성 (index.html 동적 로딩용)
    result_list = []
    png_files = sorted(list(output_dir.glob("*.png")))
    for png in png_files:
        base = png.stem
        result_list.append({
            "id": base,
            "png": f"output/{png.name}",
            "pptx": f"output/{base}.pptx"
        })
    
    with open(ROOT_PATH / "output" / "data.json", "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=4)
    print(f"\nMetadata updated with {len(result_list)} items in output/data.json")

if __name__ == "__main__":
    asyncio.run(process_images())
