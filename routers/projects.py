from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user
from core.limits import get_limits
from db import get_db
from models import Project, ProjectMember, User
from schemas import (
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberPermissionUpdate,
    ProjectMemberResponse,
    ProjectResponse,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


async def get_project_or_404(project_id: int, db: AsyncSession) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


async def get_membership(project_id: int, user_id: int, db: AsyncSession) -> ProjectMember | None:
    return (await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )).scalar_one_or_none()


async def require_project_owner(project: Project, user: User) -> None:
    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only the project owner can perform this action")


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    limits = await get_limits(db)
    if current_user.role != "admin":
        count = await db.scalar(select(func.count()).select_from(Project).where(Project.owner_id == current_user.id))
        if count >= limits.max_projects_per_user:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Project creation limit reached")
    project = Project(**data.model_dump(), owner_id=current_user.id)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    if current_user.role == "admin":
        statement = select(Project)
    else:
        statement = select(Project).outerjoin(
            ProjectMember, ProjectMember.project_id == Project.id
        ).where((Project.owner_id == current_user.id) | (ProjectMember.user_id == current_user.id)).distinct()
    return list((await db.execute(statement)).scalars().all())


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = await get_project_or_404(project_id, db)
    if current_user.role != "admin" and project.owner_id != current_user.id:
        if await get_membership(project_id, current_user.id, db) is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have access to this project")
    return project


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    project_id: int,
    data: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMember:
    project = await get_project_or_404(project_id, db)
    await require_project_owner(project, current_user)
    if data.user_id == project.owner_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The owner already has full project access")
    if await db.get(User, data.user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if await get_membership(project_id, data.user_id, db):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User is already a project member")
    member = ProjectMember(project_id=project_id, **data.model_dump())
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.patch("/{project_id}/members/{user_id}", response_model=ProjectMemberResponse)
async def update_member_permission(
    project_id: int,
    user_id: int,
    data: ProjectMemberPermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMember:
    project = await get_project_or_404(project_id, db)
    await require_project_owner(project, current_user)
    member = await get_membership(project_id, user_id, db)
    if member is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project member not found")
    member.can_edit = data.can_edit
    await db.commit()
    await db.refresh(member)
    return member
