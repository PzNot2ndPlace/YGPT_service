import os

from fastapi import APIRouter, HTTPException
from ...services.entities_extractor import entities_extractor
from ygpt_service.schemas import GenerateTextRequest

router = APIRouter(prefix="/entities", tags=["Entities extraction"])


@router.post("/get_from_text")
async def get_from_text(request: GenerateTextRequest):
    return await entities_extractor.extract_entities_from_user_text(request)


@router.get("/insecure_headers")
def insecure_headers():
    from fastapi.responses import JSONResponse
    response = JSONResponse(content={"message": "This endpoint has insecure headers!"})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Cache-Control"] = "no-store"
    return response
