from fastapi import APIRouter
from pipeline.export.csv_export import export_csv
from pipeline.export.excel_export import export_excel
router = APIRouter()

@router.post("/csv")
def create_csv_export():
    return {"file_path": export_csv()}

@router.post("/xlsx")
def create_xlsx_export():
    return {"file_path": export_excel()}
