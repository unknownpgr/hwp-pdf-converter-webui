import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import subprocess
import uuid
from io import BytesIO

app = FastAPI()

# 파일 저장 경로 설정
OUTPUT_DIR = "/tmp/files"
TEMP_DIR = "/tmp/temp"

# 디렉토리 생성
for directory in [OUTPUT_DIR, TEMP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

@app.post("/convert")
async def convert_hwp_to_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.hwp'):
        raise HTTPException(status_code=400, detail="Only HWP files are allowed")
    
    # 임시 디렉토리 생성
    temp_work_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
    os.makedirs(temp_work_dir)
    
    # 임시 파일 저장
    temp_file_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.hwp")
    pdf_file_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file.filename)[0]}.pdf")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # hwp5html 명령어로 HTML 변환
        subprocess.run([
            "hwp5html",
            "--output", temp_work_dir,
            temp_file_path
        ], check=True)
        
        # HTML 파일 경로
        html_file = os.path.join(temp_work_dir, "index.xhtml")
        css_file = os.path.join(temp_work_dir, "styles.css")

        # CSS 파일에 페이지 설정 (사이즈 레터, 마진, 패딩 없음) 추가
        with open(css_file, "a") as f:
            f.write("""
            @page {
                size: letter;
                margin: 0;
                padding: 0;
            }
            """
        )

        # HTML을 PDF로 변환
        subprocess.run([
            "weasyprint",
            html_file,
            pdf_file_path,
        ], check=True)
        
        return {"message": "Conversion successful", "pdf_path": pdf_file_path}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"HTML conversion failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 에러 발생 시에도 임시 파일 및 디렉토리 정리
        # if os.path.exists(temp_work_dir):
        #     shutil.rmtree(temp_work_dir)
        pass

@app.get("/files")
async def list_converted_files():
    try:
        files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.pdf')]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# 정적 파일 서빙 설정
app.mount("/", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
