import os
import json
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path("results")
FRONTEND_DATA = Path("frontend") / "results.json"

results_list = []
images = sorted(list(set([f.split('_')[0] for f in os.listdir(RESULTS_DIR) if f.endswith('.png')])))

for base_name in images:
    png_file = f"{base_name}_result.png"
    pptx_file = f"{base_name}_result.pptx"
    
    if os.path.exists(RESULTS_DIR / png_file) and os.path.exists(RESULTS_DIR / pptx_file):
        results_list.append({
            "original": f"{base_name}.jpg",
            "result_png": f"results/{png_file}",
            "result_pptx": f"results/{pptx_file}",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

with open(FRONTEND_DATA, 'w', encoding='utf-8') as f:
    json.dump(results_list, f, ensure_ascii=False, indent=2)

print(f"Final results.json updated with {len(results_list)} items.")
