from fastapi import FastAPI

from routers.admin import router as admin_router
from routers.auth import router as auth_router
from routers.projects import router as projects_router
from routers.tasks import router as tasks_router

app = FastAPI(title="Project Task RBAC API")
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(projects_router)
app.include_router(tasks_router)


@app.get("/")
async def root():
    return {"message": "Project Task RBAC API is running"}
