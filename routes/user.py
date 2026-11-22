from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from schema.user import UserLogin, UserRegister, UserResponse, UserUpdate
from core.utlity import DUMMY_HASH, hash_password, verify_password
from database import get_db
from model.user import User
from core.auth import create_access_token, get_current_user

def send_email(email:str):
    print(f"welcome {email}, you are now member")

route = APIRouter(prefix="/user", tags=["user"])

INVALID_CREDENTIALS = "invalid email or password"


@route.post("/register", status_code=201, response_model=UserResponse)
async def user_register(
    data: UserRegister,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    new_user = User(
        name=data.name,
        email=data.email,
        phone=data.phone,
        password_hash=await hash_password(data.password)
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="email or phone already registered")
    background_tasks.add_task(send_email, data.email)
    return new_user


@route.post("/login")
async def user_login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalars().first()

    if user is None:
        await verify_password(data.password, DUMMY_HASH)
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    if not await verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail=INVALID_CREDENTIALS)

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="account blocked")

    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


@route.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@route.patch("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user
