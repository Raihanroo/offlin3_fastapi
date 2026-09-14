from fastapi import FastAPI, status, HTTPException, Depends
from fastapi.concurrency import asynccontextmanager
from sqlalchemy import select
# from db import engine, Base, get_db
from db import get_db, init_db
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import (
    TaskResponse, TaskCreate, TaskReplace, TaskUpdate,
    UserResponse, UserCreate, UserReplace, UserUpdate,
)
from models import Task, User
from routers.auth import router as auth_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up db connection...")
    await init_db()  # Initialize the database
    yield  # Yield control back to the application
    print("Shutting down db connection...")

app = FastAPI(lifespan=lifespan)

# app = FastAPI()

app.include_router(auth_router)

# db = get_db()

@app.get("/")
async def root():
    return {"message": "Root endpoint is working!"}

# @app.get("/health", status_code=status.HTTP_200_OK)
# async def readyness_check(db: AsyncSession = Depends(get_db)):
#     return {"status": "health ok"}

@app.get("/tasks", response_model=list[TaskResponse], status_code=status.HTTP_200_OK)
async def get_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task))
    tasks = result.scalars().all()
    return tasks


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(title=task.title, description=task.description)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@app.get("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


# PUT -> full replace, sob field pathate hobe
@app.put("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def replace_task(task_id: int, task_data: TaskReplace, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.title = task_data.title
    task.description = task_data.description
    task.completed = task_data.completed

    await db.commit()
    await db.refresh(task)
    return task


# PATCH -> partial update, শুধু যা পাঠানো হবে সেটাই বদলাবে
@app.patch("/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def update_task(task_id: int, task_data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    update_data = task_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    await db.delete(task)
    await db.commit()
    return None


# ---------------- User routes ----------------

@app.get("/users", response_model=list[UserResponse], status_code=status.HTTP_200_OK)
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


@app.get("/users/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = User(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,  # note: real project e hash kore rakhte hobe
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# PUT -> full replace
@app.put("/users/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def replace_user(user_id: int, user_data: UserReplace, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.username = user_data.username
    user.email = user_data.email
    user.password = user_data.password
    user.is_active = user_data.is_active

    await db.commit()
    await db.refresh(user)
    return user


# PATCH -> partial update
@app.patch("/users/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(user_id: int, user_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    await db.delete(user)
    await db.commit()
    return None

# # query parameter -> filtering, pagination, sorting, searching
# @app.get("/tasks/")
# async def get_limited_task(skip: int = 0, limit: int = 2):
#     return db[skip: skip + limit]