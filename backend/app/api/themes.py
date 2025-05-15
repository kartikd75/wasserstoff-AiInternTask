from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from app.services.theme_detector import ThemeDetector
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
theme_detector = ThemeDetector()

@router.post("/identify")
async def identify_themes(query_results: Dict[str, Any] = Body(...)):
    """
    Identify themes from query results
    """
    try:
        # Identify themes
        themes = await theme_detector.identify_themes(query_results)
        
        return themes
    except Exception as e:
        logger.error(f"Error identifying themes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))