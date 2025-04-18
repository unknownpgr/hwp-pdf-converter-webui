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

# Set file storage paths
OUTPUT_DIR = "/tmp/files"
TEMP_DIR = "/tmp/temp"

# Create directories
for directory in [OUTPUT_DIR, TEMP_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

@app.post("/convert")
async def convert_hwp_to_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith('.hwp'):
        raise HTTPException(status_code=400, detail="Only HWP files are allowed")
    
    # Create temporary directory
    temp_work_dir = os.path.join(TEMP_DIR, str(uuid.uuid4()))
    os.makedirs(temp_work_dir)
    
    # Save temporary file
    temp_file_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.hwp")
    pdf_file_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file.filename)[0]}.pdf")
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Convert to HTML using hwp5html command
        subprocess.run([
            "hwp5html",
            "--output", temp_work_dir,
            temp_file_path
        ], check=True)
        
        # HTML file paths
        html_file = os.path.join(temp_work_dir, "index.xhtml")
        css_file = os.path.join(temp_work_dir, "styles.css")

        # Add page settings to CSS file (letter size, no margins, no padding)
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
        
        return {"message": "Conversion successful", "pdf_path": pdf_file_path}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"HTML conversion failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temporary files and directories even if error occurs
        if os.path.exists(temp_work_dir):
            shutil.rmtree(temp_work_dir)

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

# Static file serving configuration
app.mount("/", StaticFiles(directory="static"), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=80)
