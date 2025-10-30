from fastapi import APIRouter
from api.routes.v1.process_handlers import router as process_router

router = APIRouter()
router.include_router(process_router, prefix='/api', tags=['api'])
