"""
GramGPT API — routers/actions.py
Быстрые действия с аккаунтами через веб.
По ТЗ раздел 2.5: выход из чатов, отписка, удаление переписок,
прочитать все сообщения, открепление папок, карантин.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database import get_db
from routers.deps import get_current_user
from models.user import User
from models.account import TelegramAccount, AccountStatus

router = APIRouter(prefix="/actions", tags=["actions"])


# ── Schemas ──────────────────────────────────────────────────

class BulkActionRequest(BaseModel):
    account_ids: list[int]
    delay: float = 2.0


class QuarantineRequest(BaseModel):
    account_id: int
    reason: str = "ручной карантин"


# ── Helpers ──────────────────────────────────────────────────

async def _get_accounts(db, account_ids: list[int], user_id: int) -> list[TelegramAccount]:
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.user_id == user_id,
            TelegramAccount.id.in_(account_ids) if account_ids else True,
        )
    )
    return result.scalars().all()


def _to_dict(a: TelegramAccount) -> dict:
    return {
        "phone": a.phone,
        "session_file": a.session_file,
        "status": a.status.value,
        "trust_score": a.trust_score,
        "tags": a.tags or [],
        "notes": a.notes or "",
        "role": a.role.value,
        "proxy": None,
    }


# ── Single account actions ────────────────────────────────────

@router.post("/leave-chats/{account_id}")
async def leave_chats(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Выйти из всех групп и чатов одного аккаунта"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.leave_chats_bulk",
        args=[[_to_dict(acc)]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "phone": acc.phone, "action": "leave_chats"}


@router.post("/leave-channels/{account_id}")
async def leave_channels(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отписаться от всех каналов одного аккаунта"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.leave_channels_bulk",
        args=[[_to_dict(acc)]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "phone": acc.phone, "action": "leave_channels"}


@router.post("/read-all/{account_id}")
async def read_all_messages(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отметить все сообщения как прочитанные"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.read_all_bulk",
        args=[[_to_dict(acc)]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "phone": acc.phone, "action": "read_all"}


@router.post("/delete-chats/{account_id}")
async def delete_private_chats(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить личные переписки одного аккаунта"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.delete_chats_bulk",
        args=[[_to_dict(acc)]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "phone": acc.phone, "action": "delete_chats"}


@router.post("/unpin-folders/{account_id}")
async def unpin_folders(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Открепить все папки (высвободить лимиты)"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.unpin_folders_bulk",
        args=[[_to_dict(acc)]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "phone": acc.phone, "action": "unpin_folders"}


# ── Quarantine ────────────────────────────────────────────────

@router.post("/quarantine/set")
async def set_quarantine(
    body: QuarantineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Перевести аккаунт в карантин"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == body.account_id,
            TelegramAccount.user_id == current_user.id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    from datetime import datetime
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    import config as cli_config

    acc.status = AccountStatus.quarantine
    acc.quarantine_reason = body.reason
    acc.quarantine_at = datetime.utcnow()
    acc.trust_score = max(0, acc.trust_score + cli_config.TRUST_SCORE.get("system_mute", -3))
    await db.flush()

    return {
        "success": True,
        "account_id": body.account_id,
        "status": "quarantine",
        "reason": body.reason,
        "trust_score": acc.trust_score,
    }


@router.post("/quarantine/lift/{account_id}")
async def lift_quarantine(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Снять карантин с аккаунта"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == current_user.id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    acc.status = AccountStatus.active
    acc.quarantine_reason = None
    acc.quarantine_at = None
    await db.flush()

    return {
        "success": True,
        "account_id": account_id,
        "status": "active",
    }


@router.get("/quarantine")
async def list_quarantine(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список аккаунтов в карантине"""
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.user_id == current_user.id,
            TelegramAccount.status == AccountStatus.quarantine,
        )
    )
    accounts = result.scalars().all()

    return {
        "count": len(accounts),
        "accounts": [
            {
                "id": a.id,
                "phone": a.phone,
                "first_name": a.first_name,
                "username": a.username,
                "trust_score": a.trust_score,
                "quarantine_reason": a.quarantine_reason,
                "quarantine_at": a.quarantine_at.isoformat() if a.quarantine_at else None,
            }
            for a in accounts
        ]
    }


# ── Bulk actions ──────────────────────────────────────────────

@router.post("/bulk/leave-chats")
async def bulk_leave_chats(
    body: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Выйти из всех чатов для нескольких аккаунтов"""
    accounts = await _get_accounts(db, body.account_ids, current_user.id)
    if not accounts:
        raise HTTPException(status_code=400, detail="Аккаунты не найдены")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.leave_chats_bulk",
        args=[[_to_dict(a) for a in accounts]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "total": len(accounts), "action": "leave_chats"}


@router.post("/bulk/leave-channels")
async def bulk_leave_channels(
    body: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отписаться от всех каналов для нескольких аккаунтов"""
    accounts = await _get_accounts(db, body.account_ids, current_user.id)
    if not accounts:
        raise HTTPException(status_code=400, detail="Аккаунты не найдены")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.leave_channels_bulk",
        args=[[_to_dict(a) for a in accounts]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "total": len(accounts), "action": "leave_channels"}


@router.post("/bulk/read-all")
async def bulk_read_all(
    body: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Прочитать все сообщения на нескольких аккаунтах"""
    accounts = await _get_accounts(db, body.account_ids, current_user.id)
    if not accounts:
        raise HTTPException(status_code=400, detail="Аккаунты не найдены")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.read_all_bulk",
        args=[[_to_dict(a) for a in accounts]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "total": len(accounts), "action": "read_all"}


@router.post("/bulk/delete-chats")
async def bulk_delete_chats(
    body: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить личные переписки на нескольких аккаунтах"""
    accounts = await _get_accounts(db, body.account_ids, current_user.id)
    if not accounts:
        raise HTTPException(status_code=400, detail="Аккаунты не найдены")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.delete_chats_bulk",
        args=[[_to_dict(a) for a in accounts]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "total": len(accounts), "action": "delete_chats"}


@router.post("/bulk/unpin-folders")
async def bulk_unpin_folders(
    body: BulkActionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Открепить папки на нескольких аккаунтах"""
    accounts = await _get_accounts(db, body.account_ids, current_user.id)
    if not accounts:
        raise HTTPException(status_code=400, detail="Аккаунты не найдены")

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.unpin_folders_bulk",
        args=[[_to_dict(a) for a in accounts]],
        queue="bulk_actions",
    )
    return {"task_id": task.id, "total": len(accounts), "action": "unpin_folders"}
