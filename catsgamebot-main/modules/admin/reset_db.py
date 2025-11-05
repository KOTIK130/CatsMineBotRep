# modules/reset_db.py

from aiogram import Router, types, F
from config import users_collection, referrals_collection, OWNER_ID
from aiogram.filters import Command

router = Router(name="reset_db")

@router.message(Command("resetdb"), F.from_user.id == OWNER_ID)
async def reset_database(message: types.Message):
    try:
        await users_collection.delete_many({})
        await referrals_collection.delete_many({})
        await message.answer("✅ База данных успешно сброшена.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при сбросе базы данных:\n<code>{e}</code>")
