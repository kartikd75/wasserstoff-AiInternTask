from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel
from app.services.query_processor import QueryProcessor
from app.services.theme_detector import ThemeDetector
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
query_processor = QueryProcessor()
theme_detector = ThemeDetector()

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    doc_ids: Optional[List[str]] = None

@router.post("/process")
async def process_query(request: QueryRequest):
    """
    Process a query against documents
    """
    try:
        # Process query
        results = await query_processor.process_query(request.query, request.doc_ids)
        
        return results
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))