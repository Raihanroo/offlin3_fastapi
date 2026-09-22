from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from core.limits import get_limits
from db import get_db
from models import Project, Task, User
from routers.projects import get_membership, get_project_or_404
from schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(tags=["Tasks"])


async def can_edit_project(project: Project, user: User, db: AsyncSession) -> bool:
    if user.role == "admin" or project.owner_id == user.id:
        return True
    member = await get_membership(project.id, user.id, db)
    return member is not None and member.can_edit


async def can_view_task(task: Task, user: User, db: AsyncSession) -> bool:
    if user.role == "admin":
        return True
    if task.project_id is None:
        return task.assigned_to_id == user.id
    project = await db.get(Project, task.project_id)
    return project is not None and (project.owner_id == user.id or task.assigned_to_id == user.id)


async def get_task_or_404(task_id: int, db: AsyncSession) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


async def validate_assignee(project: Project, assignee_id: int, db: AsyncSession) -> None:
    assignee = await db.get(User, assignee_id)
    if assignee is None or not assignee.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Assignee must be an active user")
    if assignee_id != project.owner_id and await get_membership(project.id, assignee_id, db) is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Assignee must be a project member")


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    project = await get_project_or_404(project_id, db)
    if not await can_edit_project(project, current_user, db):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission to create tasks in this project")
    await validate_assignee(project, data.assigned_to_id, db)
    limits = await get_limits(db)
    created_count = await db.scalar(
        select(func.count()).select_from(Task).where(Task.created_by_id == current_user.id)
    )
    project_count = await db.scalar(
        select(func.count()).select_from(Task).where(Task.project_id == project_id)
    )
    if created_count >= limits.max_tasks_per_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Task creation limit reached")
    if project_count >= limits.max_tasks_per_project:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This project has reached its task limit")
    task = Task(
        title=data.title,
        description=data.description,
        project_id=project_id,
        assigned_to_id=data.assigned_to_id,
        created_by_id=current_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
async def list_project_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Task]:
    project = await get_project_or_404(project_id, db)
    statement = select(Task).where(Task.project_id == project_id)
    if current_user.role != "admin" and project.owner_id != current_user.id:
        statement = statement.where(Task.assigned_to_id == current_user.id)
    return list((await db.execute(statement)).scalars().all())


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = await get_task_or_404(task_id, db)
    if not await can_view_task(task, current_user, db):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this task")
    return task


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Task:
    task = await get_task_or_404(task_id, db)
    if task.project_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Task is not linked to a project")
    project = await get_project_or_404(task.project_id, db)
    if not await can_edit_project(project, current_user, db):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have edit permission for this project")
    update_data = data.model_dump(exclude_unset=True)
    if "assigned_to_id" in update_data:
        await validate_assignee(project, update_data["assigned_to_id"], db)
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    task = await get_task_or_404(task_id, db)
    if task.project_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Task is not linked to a project")
    project = await get_project_or_404(task.project_id, db)
    if not await can_edit_project(project, current_user, db):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have delete permission for this project")
    await db.delete(task)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
