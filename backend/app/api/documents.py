import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List
from app.core.config import settings
from app.services.ocr_service import OCRService
from app.services.vector_store import VectorStore
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
ocr_service = OCRService()
vector_store = VectorStore()

# In-memory document processing status
document_status = {}

@router.post("/upload")
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
):
    """
    Upload and process documents
    """
    try:
        results = []
        
        for file in files:
            # Generate document ID
            doc_id = f"DOC{str(uuid.uuid4())[:8].upper()}"
            
            # Check file extension
            file_ext = file.filename.split(".")[-1].lower()
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                results.append({
                    "doc_id": doc_id,
                    "file_name": file.filename,
                    "status": "error",
                    "message": f"Unsupported file type: {file_ext}"
                })
                continue
            
            # Save file to upload directory
            file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}.{file_ext}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Update status
            document_status[doc_id] = {
                "doc_id": doc_id,
                "file_name": file.filename,
                "status": "processing",
                "progress": 0
            }
            
            # Process document in background
            background_tasks.add_task(
                process_document,
                doc_id,
                file_path,
                file.filename
            )
            
            results.append({
                "doc_id": doc_id,
                "file_name": file.filename,
                "status": "processing",
                "message": "Document queued for processing"
            })
        
        return JSONResponse(
            status_code=202,
            content={"message": "Documents uploaded and queued for processing", "documents": results}
        )
    except Exception as e:
        logger.error(f"Error uploading documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{doc_id}")
async def get_document_status(doc_id: str):
    """
    Get document processing status
    """
    if doc_id in document_status:
        return document_status[doc_id]
    raise HTTPException(status_code=404, detail="Document not found")

@router.get("/list")
async def list_documents():
    """
    List all processed documents
    """
    try:
        doc_ids = vector_store.get_document_ids()
        documents = []
        
        for doc_id in doc_ids:
            metadata = vector_store.get_document_metadata(doc_id)
            if metadata:
                documents.append({
                    "doc_id": doc_id,
                    "file_name": metadata.get("file_name", "Unknown"),
                    "file_type": metadata.get("file_type", "Unknown"),
                    "total_pages": metadata.get("total_pages", 0),
                    "total_paragraphs": metadata.get("total_paragraphs", 0)
                })
        
        return {"documents": documents}
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    Delete a document (not implemented in this version)
    """
    # This would require additional implementation to remove from vector store
    raise HTTPException(status_code=501, detail="Document deletion not implemented")

# Background processing function
async def process_document(doc_id: str, file_path: str, original_filename: str):
    """
    Process document in background
    """
    try:
        # Update status
        document_status[doc_id]["status"] = "processing"
        document_status[doc_id]["progress"] = 10
        
        # Process document with OCR
        document_status[doc_id]["progress"] = 30
        document_content = ocr_service.process_document(file_path)
        
        # Update status
        document_status[doc_id]["progress"] = 60
        
        # Add to vector store
        vector_store.add_document(doc_id, document_content, file_path)
        
        # Update status
        document_status[doc_id]["status"] = "completed"
        document_status[doc_id]["progress"] = 100
        document_status[doc_id]["pages"] = len(document_content["pages"])
        
    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {str(e)}")
        document_status[doc_id]["status"] = "error"
        document_status[doc_id]["error"] = str(e)