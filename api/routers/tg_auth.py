"""
GramGPT API — routers/tg_auth.py
Веб-авторизация Telegram аккаунтов без терминала.

Поток:
  1. POST /tg-auth/send-code   — отправляет SMS/код в приложение
  2. POST /tg-auth/confirm     — подтверждает код, создаёт сессию
  3. POST /tg-auth/confirm-2fa — если нужен пароль 2FA

Сессионные данные (phone_code_hash) хранятся в Redis с TTL 10 минут.
Каждый user_id изолирован — нельзя подтвердить чужой код.
"""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from routers.deps import get_current_user
from models.user import User
from services.accounts import create_account, get_account_by_phone, sync_from_dict
import config as api_config

import importlib.util
import os

def load_cli_config():
    """Загружает корневой config.py напрямую по пути"""
    # Поднимаемся на 2 уровня вверх от текущего файла
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../config.py"))
    
    spec = importlib.util.spec_from_file_location("cli_config_external", config_path)
    cli_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli_module)
    return cli_module

router = APIRouter(prefix="/tg-auth", tags=["tg-auth"])

# ── Redis helper ─────────────────────────────────────────────
def _redis():
    import redis as redis_lib
    return redis_lib.Redis.from_url(
        __import__("os").getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True
    )


def _session_key(user_id: int, phone: str) -> str:
    return f"tg_auth:{user_id}:{phone}"


# ── Schemas ──────────────────────────────────────────────────

class SendCodeRequest(BaseModel):
    phone: str


class ConfirmCodeRequest(BaseModel):
    phone: str
    code: str


class Confirm2FARequest(BaseModel):
    phone: str
    password: str


class SendCodeResponse(BaseModel):
    phone: str
    code_type: str   # "app" | "sms" | "call"
    message: str


class AuthResult(BaseModel):
    success: bool
    phone: str
    first_name: str = ""
    username: str = ""
    account_id: int | None = None
    needs_2fa: bool = False
    message: str = ""


# ── Helpers ──────────────────────────────────────────────────

def _make_client(phone: str):
    """Создаёт Telethon-клиент с теми же параметрами что и CLI"""
    from telethon import TelegramClient
    
    # Вызываем нашу правильную функцию загрузки конфига
    cli_config = load_cli_config()

    session_path = str(cli_config.SESSIONS_DIR / phone.replace("+", ""))
    return TelegramClient(
        session_path,
        cli_config.API_ID,
        cli_config.API_HASH,
        device_model="Desktop",
        system_version="Windows 10",
        app_version="5.0.0",
        lang_code="ru",
        system_lang_code="ru",
    )


def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Endpoints ────────────────────────────────────────────────

ACTIVE_AUTH_CLIENTS = {}

# ── Endpoints ────────────────────────────────────────────────

@router.post("/send-code", response_model=SendCodeResponse)
async def send_code(
    body: SendCodeRequest,
    current_user: User = Depends(get_current_user),
):
    phone = body.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    cli_config = load_cli_config() 

    if not cli_config.API_ID or not cli_config.API_HASH:
        raise HTTPException(status_code=500, detail="TG_API_ID / TG_API_HASH не настроены на сервере")

    # Если клиент для этого номера уже висит в памяти — очищаем его
    if phone in ACTIVE_AUTH_CLIENTS:
        try:
            await ACTIVE_AUTH_CLIENTS[phone].disconnect()
        except:
            pass
        del ACTIVE_AUTH_CLIENTS[phone]

    client = _make_client(phone)

    try:
        await client.connect()

        if await client.is_user_authorized():
            await client.disconnect()
            return SendCodeResponse(
                phone=phone, code_type="already_authorized",
                message="Аккаунт уже авторизован. Можно добавить без кода."
            )

        sent = await client.send_code_request(phone)
        code_type_name = type(sent.type).__name__

        if "App" in code_type_name:
            code_type = "app"
            msg = "Код отправлен в приложение Telegram"
        elif "Sms" in code_type_name:
            code_type = "sms"
            msg = f"Код отправлен по SMS на {phone}"
        else:
            code_type = "call"
            msg = f"Код отправлен (тип: {code_type_name})"

        r = _redis()
        session_data = {
            "phone_code_hash": sent.phone_code_hash,
            "phone": phone,
        }
        r.setex(_session_key(current_user.id, phone), 600, json.dumps(session_data))

        # САМОЕ ВАЖНОЕ: Сохраняем клиента в память и НЕ отключаемся!
        ACTIVE_AUTH_CLIENTS[phone] = client

        return SendCodeResponse(phone=phone, code_type=code_type, message=msg)

    except Exception as e:
        await client.disconnect()
        err_msg = str(e)
        if "PHONE_NUMBER_INVALID" in err_msg:
            raise HTTPException(status_code=400, detail="Неверный номер телефона")
        if "FLOOD_WAIT" in err_msg:
            import re
            secs = re.search(r"\d+", err_msg)
            wait = secs.group() if secs else "?"
            raise HTTPException(status_code=429, detail=f"Слишком много попыток — подожди {wait} сек")
        raise HTTPException(status_code=500, detail=f"Ошибка Telegram: {err_msg}")


@router.post("/confirm", response_model=AuthResult)
async def confirm_code(
    body: ConfirmCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    phone = body.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    code = body.code.strip().replace(" ", "")

    r = _redis()
    raw = r.get(_session_key(current_user.id, phone))
    if not raw:
        raise HTTPException(status_code=400, detail="Сессия истекла или код не запрошен.")

    session_data = json.loads(raw)
    phone_code_hash = session_data["phone_code_hash"]

    # Достаем ТОГО ЖЕ САМОГО клиента, который запрашивал код
    client = ACTIVE_AUTH_CLIENTS.get(phone)
    if not client:
        # Резервный вариант, если сервер успел перезагрузиться
        client = _make_client(phone)
        await client.connect()

    try:
        from telethon import errors

        try:
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
        except errors.SessionPasswordNeededError:
            r.setex(_session_key(current_user.id, phone) + ":needs2fa", 600, "1")
            
            # Оставляем клиента в памяти для ввода пароля 2FA
            ACTIVE_AUTH_CLIENTS[phone] = client 
            
            return AuthResult(success=False, phone=phone, needs_2fa=True, message="Нужна 2FA.")
        except errors.PhoneCodeInvalidError:
            raise HTTPException(status_code=400, detail="Неверный код")
        except errors.PhoneCodeExpiredError:
            raise HTTPException(status_code=400, detail="Код истёк — запроси новый")

        # Успех! Получаем данные и ТЕПЕРЬ отключаемся
        me = await client.get_me()
        await client.disconnect()
        ACTIVE_AUTH_CLIENTS.pop(phone, None) # Убираем из словаря
        r.delete(_session_key(current_user.id, phone))

        cli_config = load_cli_config()
        
        # --- НАЧАЛО БЛОКА БЕЗОПАСНЫХ ИМПОРТОВ ---
        import sys, os
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)

        # Временно прячем api/config.py из кэша, чтобы trust.py и db.py загрузили корневой конфиг
        api_config_cache = sys.modules.pop('config', None)

        import trust as trust_module
        from db import make_account_template

        # Возвращаем api/config.py обратно в кэш
        if api_config_cache:
            sys.modules['config'] = api_config_cache
        # --- КОНЕЦ БЛОКА БЕЗОПАСНЫХ ИМПОРТОВ ---

        account_dict = make_account_template(phone)
        account_dict["id"] = me.id
        account_dict["first_name"] = me.first_name or ""
        account_dict["username"] = me.username or ""
        account_dict["has_photo"] = bool(me.photo)
        account_dict["session_file"] = str(cli_config.SESSIONS_DIR / phone.replace("+", "")) + ".session"
        account_dict["status"] = "active"
        account_dict["trust_score"] = trust_module.calculate(account_dict)

        db_account = await sync_from_dict(db, current_user, account_dict)

        return AuthResult(success=True, phone=phone, first_name=me.first_name or "", username=me.username or "", account_id=db_account.id, message="Успешно!")

    except HTTPException:
        raise
    except Exception as e:
        await client.disconnect()
        ACTIVE_AUTH_CLIENTS.pop(phone, None)
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.post("/confirm-2fa", response_model=AuthResult)
async def confirm_2fa(
    body: Confirm2FARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    phone = body.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    r = _redis()
    flag = r.get(_session_key(current_user.id, phone) + ":needs2fa")
    if not flag:
        raise HTTPException(status_code=400, detail="Нет ожидающей 2FA.")

    # Снова берем открытого клиента из памяти
    client = ACTIVE_AUTH_CLIENTS.get(phone)
    if not client:
        client = _make_client(phone)
        await client.connect()

    try:
        from telethon import errors
        try:
            await client.sign_in(password=body.password)
        except errors.PasswordHashInvalidError:
            raise HTTPException(status_code=400, detail="Неверный пароль 2FA")

        me = await client.get_me()
        await client.disconnect()
        ACTIVE_AUTH_CLIENTS.pop(phone, None) # Очищаем
        r.delete(_session_key(current_user.id, phone) + ":needs2fa")
        r.delete(_session_key(current_user.id, phone))

        cli_config = load_cli_config()
        
        # --- НАЧАЛО БЛОКА БЕЗОПАСНЫХ ИМПОРТОВ ---
        import sys, os
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)

        # Временно прячем api/config.py из кэша, чтобы trust.py и db.py загрузили корневой конфиг
        api_config_cache = sys.modules.pop('config', None)

        import trust as trust_module
        from db import make_account_template

        # Возвращаем api/config.py обратно в кэш
        if api_config_cache:
            sys.modules['config'] = api_config_cache
        # --- КОНЕЦ БЛОКА БЕЗОПАСНЫХ ИМПОРТОВ ---

        account_dict = make_account_template(phone)
        account_dict["id"] = me.id
        account_dict["first_name"] = me.first_name or ""
        account_dict["username"] = me.username or ""
        account_dict["session_file"] = str(cli_config.SESSIONS_DIR / phone.replace("+", "")) + ".session"
        account_dict["status"] = "active"
        account_dict["trust_score"] = trust_module.calculate(account_dict)

        db_account = await sync_from_dict(db, current_user, account_dict)

        return AuthResult(success=True, phone=phone, first_name=me.first_name or "", username=me.username or "", account_id=db_account.id, message="Авторизован (2FA)!")

    except HTTPException:
        raise
    except Exception as e:
        await client.disconnect()
        ACTIVE_AUTH_CLIENTS.pop(phone, None)
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")

@router.post("/add-already-authorized")
async def add_already_authorized(
    body: SendCodeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Добавляет аккаунт у которого уже есть .session файл на сервере.
    Используется при импорте существующих сессий.
    """
    phone = body.phone.strip()
    if not phone.startswith("+"):
        phone = "+" + phone

    client = _make_client(phone)

    try:
        await client.connect()
        if not await client.is_user_authorized():
            raise HTTPException(status_code=400, detail="Сессия не активна — авторизуйся заново")

        me = await client.get_me()
        await client.disconnect()

        cli_config = load_cli_config()
        import trust as trust_module
        from db import make_account_template

        account_dict = make_account_template(phone)
        account_dict["id"] = me.id
        account_dict["first_name"] = me.first_name or ""
        account_dict["last_name"] = me.last_name or ""
        account_dict["username"] = me.username or ""
        account_dict["has_photo"] = bool(me.photo)
        account_dict["session_file"] = str(cli_config.SESSIONS_DIR / phone.replace("+", "")) + ".session"
        account_dict["status"] = "active"
        account_dict["trust_score"] = trust_module.calculate(account_dict)

        db_account = await sync_from_dict(db, current_user, account_dict)

        return {
            "success": True,
            "account_id": db_account.id,
            "phone": phone,
            "first_name": me.first_name or "",
            "username": me.username or "",
        }

    except HTTPException:
        raise
    except Exception as e:
        try:
            await client.disconnect()
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
