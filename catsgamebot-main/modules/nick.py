# modules/nick.py

from aiogram import Router, F
from aiogram.types import Message
from config import users_collection

router = Router(name="nickname")


@router.message(F.text.startswith("/nick "))
async def set_nickname(message: Message):
    user_id = message.from_user.id
    nickname = message.text[6:].strip()

    if not nickname:
        await message.reply("Пожалуйста, укажи ник после команды. Пример: <code>/nick Громовержец</code>")
        return

    if len(nickname) > 20:
        await message.reply("Ник не должен превышать 20 символов.")
        return

    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"nickname": nickname}},
        upsert=True
    )

    await message.reply(f"Твой ник установлен как <b>{nickname}</b>.")


async def get_nickname(user_id: int, fallback_name: str = None) -> str:
    user = await users_collection.find_one({"user_id": user_id})
    if user:
        return user.get("nickname") or fallback_name or f"Игрок {user_id}"
    return fallback_name or f"Игрок {user_id}"
