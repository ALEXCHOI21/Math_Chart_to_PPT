import asyncio
import sys
import json
from pathlib import Path

ROOT_PATH = Path(r"D:\CDR_SynologyDrive\00_AI_AGENT\01_EDU\도구\수학 그래프 PPT 변환")
sys.path.append(str(ROOT_PATH))

from backend.ai_analyzer import GraphAnalyzer
from backend.png_generator import PNGGenerator

async def debug():
    analyzer = GraphAnalyzer()
    png_gen = PNGGenerator(str(ROOT_PATH / "output"))
    
    img_path = ROOT_PATH / "이미지" / "1.jpg"
    print(f"DEBUG: Analyzing {img_path}...")
    
    res = await analyzer.analyze(str(img_path))
    print("DEBUG: Analysis Result:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    
    if isinstance(res, list):
        for i, graph in enumerate(res):
            filename = f"1_{i+1}.png"
            print(f"DEBUG: Generating {filename}...")
            png_gen.generate_transparent_png(graph, filename)
    else:
        print("DEBUG: Result is not a list. Single graph processing.")
        png_gen.generate_transparent_png(res, "1_single.png")

if __name__ == "__main__":
    asyncio.run(debug())
