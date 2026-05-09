import os
import asyncio
import sys
import json
from pathlib import Path

# 프로젝트 루트 경로
ROOT_PATH = Path(r"D:\CDR_SynologyDrive\00_AI_AGENT\01_EDU\도구\수학 그래프 PPT 변환")
sys.path.append(str(ROOT_PATH))

from backend.ai_analyzer import GraphAnalyzer
from backend.converter import PPTConverter
from backend.png_generator import PNGGenerator

async def process_images():
    image_dir  = ROOT_PATH / "이미지"
    output_dir = ROOT_PATH / "output"
    output_dir.mkdir(exist_ok=True)

    analyzer = GraphAnalyzer()
    converter = PPTConverter()
    png_gen   = PNGGenerator(str(output_dir))

    # ── 이미지 파일 수집 (1.jpg, 2.jpg … 순 정렬) ──
    images = sorted(
        [f for f in image_dir.iterdir()
         if f.suffix.lower() in ('.jpg', '.jpeg', '.png')],
        key=lambda p: p.name
    )
    print(f"📂 총 {len(images)}개 이미지 발견: {[f.name for f in images]}\n")

    success_count = 0

    for img_path in images:
        stem = img_path.stem          # "1", "2", … "6"
        png_name  = f"{stem}.png"
        pptx_name = f"{stem}.pptx"

        print(f"{'─'*50}")
        print(f"🔍 [{stem}] 분석 시작: {img_path.name}")

        try:
            # ① Gemini 분석 — 이미지 1장 = 그래프 1개로 요청
            graph_data = await analyzer.analyze(str(img_path))

            # AI 가 리스트를 반환하면 첫 번째 항목만 사용 (1:1 정책)
            if isinstance(graph_data, list):
                if len(graph_data) == 0:
                    print(f"⚠️  [{stem}] 분석 결과 없음, 건너뜀")
                    continue
                graph_data = graph_data[0]

            if "error" in graph_data:
                print(f"❌ [{stem}] AI 오류: {graph_data['error']}")
                continue

            # ② 투명 PNG 생성
            print(f"🖼️  [{stem}] PNG 생성 중…")
            png_gen.generate_transparent_png(graph_data, png_name)

            # ③ PPTX 생성
            print(f"📊 [{stem}] PPTX 생성 중…")
            converter.create_ppt(graph_data, str(output_dir / pptx_name))

            print(f"✅ [{stem}] 완료! → {png_name}, {pptx_name}")
            success_count += 1

        except Exception as e:
            import traceback
            print(f"❌ [{stem}] 처리 실패: {e}")
            traceback.print_exc()

    # ── data.json 생성 (웹 UI 동적 로딩용) ──
    result_list = []
    for png_file in sorted(output_dir.glob("*.png")):
        base = png_file.stem
        result_list.append({
            "id"  : base,
            "png" : f"output/{png_file.name}",
            "pptx": f"output/{base}.pptx"
        })

    json_path = output_dir / "data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result_list, f, ensure_ascii=False, indent=4)

    print(f"\n{'═'*50}")
    print(f"🎉 변환 완료: {success_count}/{len(images)}개 성공")
    print(f"📝 메타데이터 갱신: output/data.json ({len(result_list)}개 항목)")
    print(f"{'═'*50}")

if __name__ == "__main__":
    asyncio.run(process_images())
