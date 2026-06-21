from fastapi import APIRouter
from pipeline.collector.run import collect_sample
router = APIRouter()

@router.get("")
def list_comments():
    return [item.as_dict() for item in collect_sample()]
