import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import require_role
from database import get_db
from model.audit_log import AuditLog
from model.enum import Role
from model.user import User
from schema.admin import AdminAction, AdminUserResponse

route = APIRouter(prefix="/admin", tags=["admin"])

staff = require_role(Role.moderator, Role.admin)


async def _load_target(db: AsyncSession, actor: User, user_id: uuid.UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()
    if target is None:
        raise HTTPException(status_code=404, detail="user not found")
    if target.id == actor.id:
        raise HTTPException(status_code=400, detail="cannot act on yourself")
    if target.role != Role.user and actor.role != Role.admin:
        raise HTTPException(status_code=403, detail="forbidden")
    return target


async def _finish(db: AsyncSession, actor: User, target: User, action: str, reason):
    db.add(AuditLog(actor_id=actor.id, target_id=target.id, action=action, reason=reason))
    await db.commit()
    await db.refresh(target)
    return target


@route.post("/users/{user_id}/verify", response_model=AdminUserResponse)
async def verify_user(
    user_id: uuid.UUID,
    data: AdminAction,
    actor: User = Depends(staff),
    db: AsyncSession = Depends(get_db),
):
    target = await _load_target(db, actor, user_id)
    target.phone_verified = True
    return await _finish(db, actor, target, "verify_phone", data.reason)


@route.post("/users/{user_id}/block", response_model=AdminUserResponse)
async def block_user(
    user_id: uuid.UUID,
    data: AdminAction,
    actor: User = Depends(staff),
    db: AsyncSession = Depends(get_db),
):
    target = await _load_target(db, actor, user_id)
    target.is_blocked = True
    return await _finish(db, actor, target, "block", data.reason)


@route.post("/users/{user_id}/unblock", response_model=AdminUserResponse)
async def unblock_user(
    user_id: uuid.UUID,
    data: AdminAction,
    actor: User = Depends(staff),
    db: AsyncSession = Depends(get_db),
):
    target = await _load_target(db, actor, user_id)
    target.is_blocked = False
    return await _finish(db, actor, target, "unblock", data.reason)