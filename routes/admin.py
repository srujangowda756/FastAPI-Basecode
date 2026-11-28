import uuid
import logging
from core.storage import delete_keys, profile_keys, signed_url
logger = logging.getLogger(__name__)
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


@route.post("/users/{user_id}/photo/remove", response_model=AdminUserResponse)
async def remove_photo(
    user_id: uuid.UUID,
    data: AdminAction,
    actor: User = Depends(staff),
    db: AsyncSession = Depends(get_db),
):
    target = await _load_target(db, actor, user_id)
    old_id = target.profile_photo_id
    if old_id is None:
        raise HTTPException(status_code=404, detail="no photo")
    target.profile_photo_id = None
    target = await _finish(db, actor, target, "remove_photo", data.reason)
    try:
        await delete_keys(list(profile_keys(old_id)))
    except Exception:
        logger.exception("failed to delete photo %s", old_id)
    return target


@route.get("/users/{user_id}/photo")
async def view_photo(
    user_id: uuid.UUID,
    actor: User = Depends(staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    target = result.scalars().first()
    if target is None or target.profile_photo_id is None:
        raise HTTPException(status_code=404, detail="no photo")
    db.add(AuditLog(actor_id=actor.id, target_id=target.id, action="view_photo", reason=None))
    await db.commit()
    return {"url": signed_url(profile_keys(target.profile_photo_id)[0])}
