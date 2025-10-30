from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from tortoise.contrib.fastapi import register_tortoise
from fastapi_limiter import FastAPILimiter
from database import get_config as get_db_config
from database import get_connection, start, teardown
from settings.settings import settings
from api import router


async def verify_api_key(api_key: str = Security(APIKeyHeader(name='X-API-KEY'))):
    if api_key != settings.x_auth_token.get_secret_value():
        raise HTTPException(status_code=401, detail='Unauthorized')


@asynccontextmanager
async def lifespan(_: FastAPI):
    await start(conn=get_db_config(get_connection()))


    # Для использования в других модулях
    yield

    await teardown()

app = FastAPI(title='AI Reels', lifespan=lifespan, debug=settings.prod_mode, dependencies=[Depends(verify_api_key)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(router)
register_tortoise(app=app, config=get_db_config(get_connection()), generate_schemas=True)
