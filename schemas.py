from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserResponse(UserBase):
    id: int
    is_active: bool
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserRegister(UserBase):
    password: str = Field(min_length=8)


class UserRegisterResponse(UserResponse):
    pass


class UserLogin(BaseModel):
    username: str
    password: str


class UserLoginResponse(BaseModel):
    message: str
    id: int
    username: str
    email: EmailStr
    access_token: str
    token_type: str = "bearer"


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberCreate(BaseModel):
    user_id: int
    can_edit: bool = False


class ProjectMemberPermissionUpdate(BaseModel):
    can_edit: bool


class ProjectMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    can_edit: bool

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    assigned_to_id: int


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    completed: bool | None = None
    assigned_to_id: int | None = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool
    project_id: int | None
    assigned_to_id: int | None
    created_by_id: int | None

    model_config = ConfigDict(from_attributes=True)


class SystemLimitUpdate(BaseModel):
    max_projects_per_user: int = Field(ge=1)
    max_tasks_per_user: int = Field(ge=1)
    max_tasks_per_project: int = Field(ge=1)


class SystemLimitResponse(SystemLimitUpdate):
    id: int

    model_config = ConfigDict(from_attributes=True)
