"""
GramGPT API — routers/channels.py
Управление каналами через веб.
По ТЗ раздел 2.3: создание, закрепление каналов.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from database import get_db
from routers.deps import get_current_user
from models.user import User
from models.account import TelegramAccount

router = APIRouter(prefix="/channels", tags=["channels"])


# ── Schemas ──────────────────────────────────────────────────

class CreateChannelRequest(BaseModel):
    account_id: int
    title: str
    description: str = ""
    username: str = ""


class BatchCreateRequest(BaseModel):
    account_ids: list[int]
    title_template: str          # "Канал {name}" или "Канал {n}"
    description: str = ""
    delay: float = 4.0


class PinChannelRequest(BaseModel):
    account_id: int
    channel_link: str            # @username или https://t.me/...


class PinExistingRequest(BaseModel):
    account_ids: list[int]
    channel_link: str


# ── Helper ───────────────────────────────────────────────────

async def _get_account(db, account_id, user_id) -> TelegramAccount:
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id == account_id,
            TelegramAccount.user_id == user_id,
        )
    )
    acc = result.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    return acc


def _to_dict(a: TelegramAccount) -> dict:
    return {
        "phone": a.phone,
        "session_file": a.session_file,
        "channels": a.channels or [],
        "first_name": a.first_name or "",
    }


# ── Endpoints ────────────────────────────────────────────────

@router.get("/accounts/{account_id}")
async def get_my_channels(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Список каналов которыми владеет аккаунт"""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    import channel_manager as ch

    acc = await _get_account(db, account_id, current_user.id)
    channels = await ch.get_my_channels(_to_dict(acc))

    # Обновляем в БД
    if channels:
        acc.channels = channels
        await db.flush()

    return {"account_id": account_id, "channels": channels}


@router.post("/create")
async def create_channel(
    body: CreateChannelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Создать новый канал от имени аккаунта.
    По ТЗ: создание личных каналов.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    import channel_manager as ch

    acc = await _get_account(db, body.account_id, current_user.id)
    acc_dict = _to_dict(acc)

    channel = await ch.create_channel(
        acc_dict, body.title, body.description, body.username
    )

    if not channel:
        raise HTTPException(status_code=500, detail="Не удалось создать канал")

    # Сохраняем канал в БД
    channels = acc.channels or []
    channels.append(channel)
    acc.channels = channels
    await db.flush()

    return {"success": True, "channel": channel}


@router.post("/batch-create")
async def batch_create_channels(
    body: BatchCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Создать каналы для нескольких аккаунтов через Celery.
    По ТЗ: создание каналов пакетно.
    """
    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.user_id == current_user.id,
            TelegramAccount.id.in_(body.account_ids),
        )
    )
    accounts = result.scalars().all()

    accounts_data = [_to_dict(a) for a in accounts]

    from celery import current_app
    task = current_app.send_task(
        "tasks.bulk_tasks.create_channels_bulk",
        args=[accounts_data, body.title_template, body.description, body.delay],
        queue="bulk_actions",
    )

    return {
        "task_id": task.id,
        "total": len(accounts_data),
        "message": f"Создание каналов для {len(accounts_data)} аккаунтов запущено"
    }


@router.post("/pin")
async def pin_channel(
    body: PinChannelRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Закрепить канал в профиле аккаунта.
    По ТЗ: закрепление личных каналов в профиле.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    import channel_manager as ch

    acc = await _get_account(db, body.account_id, current_user.id)
    ok = await ch.pin_channel_to_profile(_to_dict(acc), body.channel_link)

    return {
        "success": ok,
        "account_id": body.account_id,
        "channel_link": body.channel_link,
    }


@router.post("/pin-existing")
async def pin_existing_channel(
    body: PinExistingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Закрепить существующий канал на несколько аккаунтов.
    По ТЗ: закрепление существующих каналов без создания новых.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
    import channel_manager as ch

    result = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.user_id == current_user.id,
            TelegramAccount.id.in_(body.account_ids),
        )
    )
    accounts = result.scalars().all()

    results = []
    for acc in accounts:
        ok = await ch.pin_existing_channel(_to_dict(acc), body.channel_link)
        results.append({"phone": acc.phone, "success": ok})

    return {
        "channel_link": body.channel_link,
        "results": results,
        "success_count": sum(1 for r in results if r["success"]),
    }
