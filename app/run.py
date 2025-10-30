import uvicorn
from settings.settings import settings
from setup import app

if __name__ == '__main__':
    uvicorn.run(app, host=settings.rest_host, port=settings.rest_port)
