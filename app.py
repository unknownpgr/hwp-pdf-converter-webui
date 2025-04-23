import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from typing import List, Dict
import subprocess
import uuid
from io import BytesIO
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib

app = FastAPI()

# Set file storage paths
BASE_DIR = "/tmp/files"
TEMP_DIR = "/tmp/temp"

# Create directories
for directory in [BASE_DIR, TEMP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_file_hash(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()

def convert_single_file(file_content: bytes, file_hash: str):
    try:
        # Create temporary directory
        temp_work_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
        os.makedirs(temp_work_dir)
        
        # Save HWP file
        hwp_file_path = os.path.join(temp_work_dir, f"{file_hash}.hwp")
        with open(hwp_file_path, "wb") as f:
            f.write(file_content)
        
        # Convert to HTML using hwp5html command
        subprocess.run([
            "hwp5html",
            "--output", temp_work_dir,
            hwp_file_path
        ], check=True)
        
        # HTML file paths
        html_file = os.path.join(temp_work_dir, "index.xhtml")
        css_file = os.path.join(temp_work_dir, "styles.css")

        # Add page settings to CSS file
        with open(css_file, "a") as f:
            f.write("""
            @page {
                size: letter;
                margin: 0;
                padding: 0;
            }
            """
        )

        # Convert HTML to PDF
        pdf_file_path = os.path.join(BASE_DIR, f"{file_hash}.pdf")
        subprocess.run([
            "weasyprint",
            html_file,
            pdf_file_path,
        ], check=True)
        
        return True
        
    except Exception as e:
        print(f"Error converting file: {str(e)}")
        return False
    finally:
        if os.path.exists(temp_work_dir):
            shutil.rmtree(temp_work_dir)

@app.post("/convert")
async def convert_hwp_to_pdf(files: List[UploadFile] = File(...)):
    try:
        converted_files = []
        
        for file in files:
            if not file.filename.endswith('.hwp'):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")
            
            # Read file content
            file_content = await file.read()
            file_hash = get_file_hash(file_content)
            
            # Check if PDF already exists
            pdf_path = os.path.join(BASE_DIR, f"{file_hash}.pdf")
            if not os.path.exists(pdf_path):
                # Convert file
                success = await asyncio.to_thread(convert_single_file, file_content, file_hash)
                if not success:
                    raise HTTPException(status_code=500, detail=f"Failed to convert file: {file.filename}")
            
            converted_files.append(f"{file_hash}.pdf")
        
        return {"files": converted_files}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(BASE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return FileResponse("static/index.html")

# Static file serving configuration
app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
