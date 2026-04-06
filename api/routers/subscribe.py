"""
GramGPT API — routers/subscribe.py
Предподготовка: подписка аккаунтов на каналы перед кампанией.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from routers.deps import get_current_user
from models.user import User
from models.account import TelegramAccount
from models.subscribe_task import SubscribeTask

router = APIRouter(prefix="/subscribe", tags=["subscribe"])


# ── Schemas ──────────────────────────────────────────────────

class SubscribeCreate(BaseModel):
    account_ids: list[int]
    channels: list[str]        # @username или ссылки, по одному
    total_minutes: int = 240   # За сколько минут подписать (по умолч. 4 часа)


# ── Endpoints ────────────────────────────────────────────────

@router.get("/tasks")
async def list_subscribe_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SubscribeTask)
        .where(SubscribeTask.user_id == current_user.id)
        .order_by(SubscribeTask.created_at.desc())
    )
    tasks = result.scalars().all()

    out = []
    for t in tasks:
        # Подтягиваем имена аккаунтов
        acc_names = {}
        if t.account_ids:
            acc_r = await db.execute(
                select(TelegramAccount).where(TelegramAccount.id.in_(t.account_ids))
            )
            for a in acc_r.scalars().all():
                acc_names[a.id] = a.first_name or a.phone

        out.append({
            "id": t.id,
            "account_ids": t.account_ids or [],
            "account_names": acc_names,
            "channels": t.channels or [],
            "total_minutes": t.total_minutes,
            "status": t.status,
            "progress": t.progress,
            "subscribed": t.subscribed,
            "failed": t.failed,
            "skipped": t.skipped,
            "error": t.error,
            "results": t.results or [],
            "total_pairs": len(t.account_ids or []) * len(t.channels or []),
            "started_at": (t.started_at.isoformat() + "Z") if t.started_at else None,
            "finished_at": (t.finished_at.isoformat() + "Z") if t.finished_at else None,
            "created_at": (t.created_at.isoformat() + "Z"),
        })

    return out


@router.post("/tasks")
async def create_subscribe_task(
    body: SubscribeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Создать задачу предподписки."""
    if not body.account_ids:
        raise HTTPException(status_code=400, detail="Выбери аккаунты")
    if not body.channels:
        raise HTTPException(status_code=400, detail="Укажи каналы")
    if body.total_minutes < 1:
        raise HTTPException(status_code=400, detail="Время минимум 1 минута")

    # Проверяем аккаунты
    acc_r = await db.execute(
        select(TelegramAccount).where(
            TelegramAccount.id.in_(body.account_ids),
            TelegramAccount.user_id == current_user.id,
        )
    )
    valid_ids = [a.id for a in acc_r.scalars().all()]
    if not valid_ids:
        raise HTTPException(status_code=400, detail="Аккаунты не найдены")

    # Нормализуем каналы
    channels = []
    for ch in body.channels:
        ch = ch.strip()
        if not ch:
            continue
        if ch.startswith("@"):
            ch = ch[1:]
        elif "t.me/" in ch:
            ch = ch.split("t.me/")[-1].split("/")[0].replace("@", "")
        channels.append(ch)

    if not channels:
        raise HTTPException(status_code=400, detail="Нет валидных каналов")

    task = SubscribeTask(
        user_id=current_user.id,
        account_ids=valid_ids,
        channels=channels,
        total_minutes=body.total_minutes,
    )
    db.add(task)
    await db.flush()

    total_pairs = len(valid_ids) * len(channels)

    return {
        "id": task.id,
        "total_pairs": total_pairs,
        "accounts": len(valid_ids),
        "channels": len(channels),
        "total_minutes": body.total_minutes,
        "message": f"Задача создана: {total_pairs} подписок за ~{body.total_minutes} мин",
    }


@router.post("/tasks/{task_id}/run")
async def run_subscribe_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Запустить подписку в фоне через Celery."""
    result = await db.execute(
        select(SubscribeTask).where(
            SubscribeTask.id == task_id,
            SubscribeTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    if task.status == "running":
        raise HTTPException(status_code=400, detail="Задача уже запущена")

    # Запускаем через Celery
    from celery_app import celery_app
    celery_task = celery_app.send_task(
        "tasks.subscribe_tasks.run_subscribe",
        args=[{
            "account_ids": task.account_ids,
            "channels": task.channels,
            "total_minutes": task.total_minutes,
            "task_id": task.id,
            "user_id": current_user.id,
        }],
        queue="bulk_actions",
    )

    task.status = "running"
    task.started_at = datetime.utcnow()
    await db.flush()

    return {
        "celery_task_id": celery_task.id,
        "message": f"Подписка запущена. ~{task.total_minutes} мин на {len(task.account_ids) * len(task.channels)} подписок",
    }


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_subscribe_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SubscribeTask).where(
            SubscribeTask.id == task_id,
            SubscribeTask.user_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if task:
        await db.delete(task)
        await db.flush()
