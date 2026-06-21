from fastapi import APIRouter
router = APIRouter()

@router.get("")
def list_schedules():
    return [{"time": "08:00", "timezone": "Asia/Jakarta"}, {"time": "18:00", "timezone": "Asia/Jakarta"}]
