from fastapi import APIRouter, status

from app.api.responses.common import MessageResponse

from .routes import init_routers

api_router = APIRouter()

init_routers(api_router)


@api_router.get("/ping", status_code=status.HTTP_200_OK, response_model=MessageResponse)
async def root():
    return {"message": "Hello"}
