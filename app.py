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

app = FastAPI()

# Set file storage paths
BASE_DIR = "/tmp/files"
TEMP_DIR = "/tmp/temp"

# Global conversion status
CONVERSION_SESSIONS = {}

# Create directories
for directory in [BASE_DIR, TEMP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_session_dir(session_id: str) -> str:
    return os.path.join(BASE_DIR, session_id)

def convert_single_file(file_path: str, pdf_file_path: str, session_id: str):
    try:
        # Create temporary directory
        temp_work_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
        os.makedirs(temp_work_dir)
        
        # Convert to HTML using hwp5html command
        subprocess.run([
            "hwp5html",
            "--output", temp_work_dir,
            file_path
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
        subprocess.run([
            "weasyprint",
            html_file,
            pdf_file_path,
        ], check=True)
        
        CONVERSION_SESSIONS[session_id]['completed_files'].append(os.path.basename(file_path))
        
        # Update overall status
        if len(CONVERSION_SESSIONS[session_id]['completed_files']) + len(CONVERSION_SESSIONS[session_id]['failed_files']) == len(CONVERSION_SESSIONS[session_id]['total_files']):
            if CONVERSION_SESSIONS[session_id]['failed_files']:
                CONVERSION_SESSIONS[session_id]['status'] = 'error'
                CONVERSION_SESSIONS[session_id]['message'] = f"Some files failed to convert: {', '.join(CONVERSION_SESSIONS[session_id]['failed_files'])}"
            else:
                CONVERSION_SESSIONS[session_id]['status'] = 'completed'
        else:
            CONVERSION_SESSIONS[session_id]['status'] = 'processing'
        
    except Exception as e:
        CONVERSION_SESSIONS[session_id]['failed_files'].append(os.path.basename(file_path))
        CONVERSION_SESSIONS[session_id]['status'] = 'error'
        CONVERSION_SESSIONS[session_id]['message'] = str(e)
    finally:
        if os.path.exists(temp_work_dir):
            shutil.rmtree(temp_work_dir)

@app.post("/convert")
async def convert_hwp_to_pdf(files: List[UploadFile] = File(...)):
    # Generate session ID
    session_id = str(uuid.uuid4())
    session_dir = get_session_dir(session_id)
    os.makedirs(session_dir, exist_ok=True)
    
    # Initialize session status
    CONVERSION_SESSIONS[session_id] = {
        'status': 'processing',
        'total_files': [file.filename for file in files],
        'completed_files': [],
        'failed_files': [],
        'message': None
    }
    
    # Validate files and save them
    temp_files = []
    try:
        for file in files:
            if not file.filename.endswith('.hwp'):
                raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}")
            
            # Save temporary file
            temp_file_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.hwp")
            pdf_file_path = os.path.join(session_dir, f"{os.path.splitext(file.filename)[0]}.pdf")
            
            # Read file content and write to temporary file
            file_content = file.file.read()
            with open(temp_file_path, "wb") as buffer:
                buffer.write(file_content)
            
            temp_files.append((temp_file_path, pdf_file_path))
        
        # Start conversion in background
        for temp_file_path, pdf_file_path in temp_files:
            asyncio.create_task(asyncio.to_thread(convert_single_file, temp_file_path, pdf_file_path, session_id))
        
        return {"session_id": session_id, "message": "Conversion started"}
    
    except Exception as e:
        # Clean up temporary files if error occurs
        for temp_file_path, _ in temp_files:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversion-status/{session_id}")
async def get_conversion_status(session_id: str):
    if session_id not in CONVERSION_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return CONVERSION_SESSIONS[session_id]

@app.get("/files/{session_id}")
async def list_converted_files(session_id: str):
    try:
        session_dir = get_session_dir(session_id)
        if not os.path.exists(session_dir):
            raise HTTPException(status_code=404, detail="Session not found")
            
        files = [f for f in os.listdir(session_dir) if f.endswith('.pdf')]
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{session_id}/{filename}")
async def download_file(session_id: str, filename: str):
    file_path = os.path.join(get_session_dir(session_id), filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/view/{session_id}/{filename}")
async def view_file(session_id: str, filename: str):
    file_path = os.path.join(get_session_dir(session_id), filename)
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
