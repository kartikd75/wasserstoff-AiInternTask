import os
import shutil
from app.services.ocr_service import OCRService
from app.services.vector_store import VectorStore
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for coordinating document processing"""
    
    def __init__(self):
        """Initialize the document processor"""
        self.ocr_service = OCRService()
        self.vector_store = VectorStore()
    
    async def process_document(self, doc_id, file_path):
        """
        Process a document end-to-end
        
        Args:
            doc_id: Document ID
            file_path: Path to the document file
            
        Returns:
            dict: Processing result
        """
        try:
            # Extract text content using OCR
            document_content = self.ocr_service.process_document(file_path)
            
            # Add document to vector store
            self.vector_store.add_document(doc_id, document_content, file_path)
            
            # Move file to processed directory
            processed_path = os.path.join(settings.PROCESSED_DIR, os.path.basename(file_path))
            shutil.move(file_path, processed_path)
            
            return {
                "doc_id": doc_id,
                "status": "completed",
                "file_path": processed_path,
                "pages": len(document_content["pages"]),
                "paragraphs": sum(len(page["paragraphs"]) for page in document_content["pages"])
            }
        except Exception as e:
            logger.error(f"Error processing document {doc_id}: {str(e)}")
            
            # Move file to processed directory even on failure
            processed_path = os.path.join(settings.PROCESSED_DIR, os.path.basename(file_path))
            if os.path.exists(file_path):
                shutil.move(file_path, processed_path)
                
            raise