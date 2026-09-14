# schema
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

    model_config = ConfigDict(from_attributes=True)

class TaskCreate(BaseModel):
    title: str
    description: str

# PUT -> full replace, sob field required
class TaskReplace(BaseModel):
    title: str
    description: str
    completed: bool = False

# PATCH -> partial update, sob field optional
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

# PUT -> full replace
class UserReplace(UserBase):
    password: str
    is_active: bool = True

# PATCH -> partial update
class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ---------------- Auth schemas ----------------

class UserRegister(UserBase):
    """Registration er jonno input schema (username, email, password)."""
    password: str


class UserRegisterResponse(BaseModel):
    """Registration success e ei shape er data ferot jabe (password kokhono na)."""
    id: int
    username: str
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Login er jonno input schema."""
    username: str
    password: str


class UserLoginResponse(BaseModel):
    """Login success e ei shape er data ferot jabe."""
    message: str
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)