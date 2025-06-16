from fastapi import FastAPI
from .api.endpoints import entities

app = FastAPI()
app.include_router(entities.router)
