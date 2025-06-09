from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import shutil
from typing import Optional, Dict, Any, Literal
from extract import main as extract_main
import uuid

app = FastAPI(title="Document Extractor API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractRequest(BaseModel):
    url: str
    mode: Literal["pdf", "txt"] = "pdf"

class ExtractResponse(BaseModel):
    task_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    task_id: str
    status: str
    message: str
    file_path: Optional[str] = None

# In-memory storage for task status (in production, use Redis or database)
tasks: Dict[str, Dict[str, Any]] = {}

async def extract_task(task_id: str, url: str, mode: Literal["pdf", "txt"]):
    """Background task to extract documents"""
    try:
        tasks[task_id] = {
            "status": "processing",
            "message": "Extracting documents...",
            "file_path": None
        }
        
        # Create unique output directory for this task
        output_dir = f"extracted_documents_{task_id}"
        
        # Run extraction
        extract_main(url, mode)
        
        # Move files to task-specific directory
        if os.path.exists("extracted_documents"):
            shutil.move("extracted_documents", output_dir)
        
        # Find the final file
        final_file = None
        if mode == "pdf":
            final_file = os.path.join(output_dir, "final.pdf")
        else:
            final_file = os.path.join(output_dir, "final.txt")
        
        if os.path.exists(final_file):
            tasks[task_id] = {
                "status": "completed",
                "message": "Extraction completed successfully",
                "file_path": final_file
            }
        else:
            tasks[task_id] = {
                "status": "failed",
                "message": "Final file not found",
                "file_path": None
            }
    
    except Exception as e:
        tasks[task_id] = {
            "status": "failed",
            "message": f"Extraction failed: {str(e)}",
            "file_path": None
        }

@app.post("/extract", response_model=ExtractResponse)
async def extract_documents(request: ExtractRequest, background_tasks: BackgroundTasks):
    """Start document extraction from URL"""
    task_id = str(uuid.uuid4())
    
    # Start background task
    background_tasks.add_task(extract_task, task_id, request.url, request.mode)
    
    return ExtractResponse(
        task_id=task_id,
        status="started",
        message="Extraction started"
    )

@app.get("/status/{task_id}", response_model=StatusResponse)
async def get_task_status(task_id: str):
    """Get status of extraction task"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return StatusResponse(
        task_id=task_id,
        status=task["status"],
        message=task["message"],
        file_path=task.get("file_path")
    )

@app.get("/view/{task_id}")
async def view_file(task_id: str):
    """View extracted file in browser (for PDF preview)"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    if task["status"] != "completed" or not task["file_path"]:
        raise HTTPException(status_code=400, detail="File not ready for viewing")
    
    file_path = task["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Read file content
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Determine content type
    if file_path.endswith('.pdf'):
        media_type = 'application/pdf'
    else:
        media_type = 'text/plain'
    
    # Return file content with proper headers for inline viewing
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Accept-Ranges": "bytes",
            "X-Content-Type-Options": "nosniff"
        }
    )

@app.get("/download/{task_id}")
async def download_file(task_id: str):
    """Download extracted file"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    if task["status"] != "completed" or not task["file_path"]:
        raise HTTPException(status_code=400, detail="File not ready for download")
    
    file_path = task["file_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    filename = os.path.basename(file_path)
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/pdf' if filename.endswith('.pdf') else 'text/plain'
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 