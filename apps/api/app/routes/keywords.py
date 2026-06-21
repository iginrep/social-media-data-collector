from fastapi import APIRouter
router = APIRouter()

@router.get("")
def list_keywords():
    return [
        {"keyword": "bni sekuritas", "target_entity": "bni_sekuritas"},
        {"keyword": "bions", "target_entity": "bions"},
        {"keyword": "bions app", "target_entity": "bions"},
        {"keyword": "bions error", "target_entity": "bions"},
    ]
