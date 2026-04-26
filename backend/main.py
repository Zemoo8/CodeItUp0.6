from fastapi import FastAPI
from routes.projects import router as projects_router
from routes.inventory import router as inventory_router
from routes.plan import router as plan_router

app = FastAPI()

app.include_router(projects_router)
app.include_router(inventory_router)
app.include_router(plan_router)