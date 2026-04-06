"""
GramGPT API — models/subscribe_task.py
Задача предподготовки: подписка аккаунтов на каналы перед кампанией.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class SubscribeTask(Base):
    __tablename__ = "subscribe_tasks"

    id:           Mapped[int]              = mapped_column(Integer, primary_key=True)
    user_id:      Mapped[int]              = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_ids:  Mapped[list]             = mapped_column(JSON, default=list)
    channels:     Mapped[list]             = mapped_column(JSON, default=list)
    total_minutes:Mapped[int]              = mapped_column(Integer, default=240)
    status:       Mapped[str]              = mapped_column(String(32), default="pending")  # pending | running | done | error
    progress:     Mapped[int]              = mapped_column(Integer, default=0)             # 0-100%
    subscribed:   Mapped[int]              = mapped_column(Integer, default=0)
    failed:       Mapped[int]              = mapped_column(Integer, default=0)
    skipped:      Mapped[int]              = mapped_column(Integer, default=0)
    error:        Mapped[Optional[str]]    = mapped_column(Text, nullable=True)
    results:      Mapped[list]             = mapped_column(JSON, default=list)
    started_at:   Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at:  Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at:   Mapped[datetime]           = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SubscribeTask #{self.id} {self.status} {self.subscribed}/{len(self.channels or [])}>"
