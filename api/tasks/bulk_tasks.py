"""
GramGPT API — tasks/bulk_tasks.py
Celery задачи для пакетных операций.
Очередь: bulk_actions
"""

import asyncio
import sys
import os

from celery_app import celery_app

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================================
# ПРОФИЛИ
# ============================================================

@celery_app.task(bind=True, name="tasks.bulk_tasks.update_profiles_bulk")
def update_profiles_bulk(self, accounts: list[dict],
                         first_name: str = None,
                         last_name: str = None,
                         bio: str = None) -> dict:
    """Пакетное обновление профилей"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Обновляю профиль {phone}...",
            }
        )
        try:
            import profile_manager as pm
            ok = run_async(pm.update_profile(account, first_name=first_name,
                                             last_name=last_name, bio=bio))
            results.append({"phone": phone, "success": ok})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    success = sum(1 for r in results if r.get("success"))
    return {"total": total, "success": success, "results": results}


@celery_app.task(bind=True, name="tasks.bulk_tasks.set_avatars_bulk")
def set_avatars_bulk(self, accounts: list[dict], image_path: str) -> dict:
    """Пакетная установка аватарок"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Ставлю аватарку {phone}...",
            }
        )
        try:
            import profile_manager as pm
            ok = run_async(pm.set_avatar(account, image_path))
            results.append({"phone": phone, "success": ok})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    success = sum(1 for r in results if r.get("success"))
    return {"total": total, "success": success, "results": results}


# ============================================================
# БЫСТРЫЕ ДЕЙСТВИЯ
# ============================================================

@celery_app.task(bind=True, name="tasks.bulk_tasks.leave_chats_bulk")
def leave_chats_bulk(self, accounts: list[dict]) -> dict:
    """Пакетный выход из всех чатов"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Выхожу из чатов {phone}...",
            }
        )
        try:
            import actions
            run_async(actions.leave_all_chats(account))
            results.append({"phone": phone, "success": True})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    return {"total": total, "success": sum(1 for r in results if r.get("success")), "results": results}


@celery_app.task(bind=True, name="tasks.bulk_tasks.leave_channels_bulk")
def leave_channels_bulk(self, accounts: list[dict]) -> dict:
    """Пакетная отписка от всех каналов"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Отписываюсь от каналов {phone}...",
            }
        )
        try:
            import actions
            run_async(actions.leave_all_channels(account))
            results.append({"phone": phone, "success": True})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    return {"total": total, "success": sum(1 for r in results if r.get("success")), "results": results}


@celery_app.task(bind=True, name="tasks.bulk_tasks.read_all_bulk")
def read_all_bulk(self, accounts: list[dict]) -> dict:
    """Пакетное прочтение всех сообщений"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Читаю сообщения {phone}...",
            }
        )
        try:
            import actions
            run_async(actions.read_all_messages(account))
            results.append({"phone": phone, "success": True})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    return {"total": total, "success": sum(1 for r in results if r.get("success")), "results": results}


@celery_app.task(bind=True, name="tasks.bulk_tasks.delete_chats_bulk")
def delete_chats_bulk(self, accounts: list[dict]) -> dict:
    """Пакетное удаление личных переписок"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Удаляю переписки {phone}...",
            }
        )
        try:
            import actions
            run_async(actions.delete_private_chats(account))
            results.append({"phone": phone, "success": True})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    return {"total": total, "success": sum(1 for r in results if r.get("success")), "results": results}


@celery_app.task(bind=True, name="tasks.bulk_tasks.unpin_folders_bulk")
def unpin_folders_bulk(self, accounts: list[dict]) -> dict:
    """Пакетное открепление папок"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Открепляю папки {phone}...",
            }
        )
        try:
            import actions
            run_async(actions.unpin_folders(account))
            results.append({"phone": phone, "success": True})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    return {"total": total, "success": sum(1 for r in results if r.get("success")), "results": results}


# ============================================================
# БЕЗОПАСНОСТЬ
# ============================================================

@celery_app.task(bind=True, name="tasks.bulk_tasks.set_2fa_bulk")
def set_2fa_bulk(self, accounts: list[dict], password: str, hint: str = "") -> dict:
    """Пакетная установка 2FA"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Устанавливаю 2FA {phone}...",
            }
        )
        try:
            import security
            ok = run_async(security.set_2fa(account, password, hint))
            results.append({"phone": phone, "success": ok})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    success = sum(1 for r in results if r.get("success"))
    return {"total": total, "success": success, "results": results}


@celery_app.task(bind=True, name="tasks.bulk_tasks.terminate_sessions_bulk")
def terminate_sessions_bulk(self, accounts: list[dict]) -> dict:
    """Пакетное завершение сторонних сессий"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Завершаю сессии {phone}...",
            }
        )
        try:
            import security
            run_async(security.terminate_other_sessions(account))
            results.append({"phone": phone, "success": True})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

    return {"total": total, "success": sum(1 for r in results if r.get("success")), "results": results}


# ============================================================
# КАНАЛЫ
# ============================================================

@celery_app.task(bind=True, name="tasks.bulk_tasks.create_channels_bulk")
def create_channels_bulk(self, accounts: list[dict], title_template: str,
                         description: str = "", delay: float = 4.0) -> dict:
    """Пакетное создание каналов"""
    total = len(accounts)
    results = []

    for i, account in enumerate(accounts):
        phone = account.get("phone", "?")
        name = account.get("first_name", phone)
        title = title_template.replace("{n}", str(i + 1)).replace("{name}", name)

        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1, "total": total,
                "percent": int((i + 1) / total * 100),
                "message": f"[{i+1}/{total}] Создаю канал '{title}' для {phone}...",
            }
        )
        try:
            import channel_manager as ch
            channel = run_async(ch.create_channel(account, title, description))
            results.append({"phone": phone, "success": bool(channel), "channel": channel})
        except Exception as e:
            results.append({"phone": phone, "success": False, "error": str(e)})

        if i < total - 1:
            import time
            time.sleep(delay)

    success = sum(1 for r in results if r.get("success"))
    return {"total": total, "success": success, "results": results}