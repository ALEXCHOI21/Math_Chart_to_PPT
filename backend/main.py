import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ai_analyzer import GraphAnalyzer
from converter import PPTConverter

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = GraphAnalyzer()
converter = PPTConverter()

UPLOAD_DIR = "temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Only images are allowed")

    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    output_path = os.path.join(UPLOAD_DIR, f"{file_id}.pptx")

    with open(input_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        # 1. AI 분석
        graph_data = await analyzer.analyze(input_path)
        
        # 2. PPT 생성
        converter.create_ppt(graph_data, output_path)

        return {
            "success": True,
            "file_id": file_id,
            "data": graph_data,
            "download_url": f"/download/{file_id}"
        }
    except Exception as e:
        print(f"Error processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    path = os.path.join(UPLOAD_DIR, f"{file_id}.pptx")
    if os.path.exists(path):
        return FileResponse(path, filename="math_graph.pptx", media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation")
    raise HTTPException(status_code=404, detail="File not found")

# 정적 파일 서비스 (Frontend)
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
