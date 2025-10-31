from fastapi import APIRouter
from api.routes.v1.process_handlers import router as process_router
from api.routes.v1.hhru_handlers import router as hhru_router
from api.routes.v1.runware_handlers import router as runware_router

router = APIRouter()
router.include_router(process_router, prefix='', tags=['llm'])
router.include_router(hhru_router, prefix='', tags=['hhru'])
router.include_router(runware_router, prefix='', tags=['runware'])
