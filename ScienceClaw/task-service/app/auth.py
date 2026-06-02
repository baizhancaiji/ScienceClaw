"""Authentication helpers for task-service routes."""
from __future__ import annotations

import time
from typing import Optional

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel

from app.core.db import db


class User(BaseModel):
    id: str
    username: str
    role: str = "user"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


async def get_current_user(request: Request) -> Optional[User]:
    auth = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None

    session_id = auth.split(" ", 1)[1].strip()
    if not session_id:
        return None

    session_doc = await db.get_collection("user_sessions").find_one({"_id": session_id})
    if not session_doc:
        return None

    if int(session_doc.get("expires_at") or 0) < int(time.time()):
        await db.get_collection("user_sessions").delete_one({"_id": session_id})
        return None

    return User(
        id=str(session_doc.get("user_id") or ""),
        username=str(session_doc.get("username") or ""),
        role=str(session_doc.get("role") or "user"),
    )


async def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def owner_filter(user: User) -> dict:
    return {} if user.is_admin else {"user_id": user.id}
