# modules/reset.py

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import users_collection
from datetime import datetime

router = Router(name="reset")

@router.message(F.text == "/reset")
async def confirm_reset(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Подтвердить сброс", callback_data="confirm_reset")
    kb.button(text="❌ Отмена", callback_data="cancel_reset")
    await message.answer(
        "⚠️ Вы уверены, что хотите сбросить весь прогресс?\nЭто действие необратимо.",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "confirm_reset")
async def reset_user(callback: CallbackQuery):
    user_id = callback.from_user.id
    user = await users_collection.find_one({"user_id": user_id})
    
    default_name = callback.from_user.first_name

    default_user = {
        "user_id": user_id,
        "name": default_name,
        "nickname": default_name,
        "created_at": datetime.utcnow(),
        "rod_level": 1,
        "money": 0,
        "fish_inventory": {},
        "total_fish_caught": 0,
        "sea_stars": 0,
        "cookies": 0,
        "fish_multiplier": 1.0,
        "star_chance": 5.0,
        "luck_x2": 10.0,
        "materials": {"wood": 0, "rope": 0, "metal": 0, "crystal": 0},
        "cases": {"can": 0, "chest": 0, "star_box": 0, "material_bag": 0, "weapon_box": 0, "legendary_safe": 0},
        "achievements": [],
        "boosters": {},
        "workers": [],
        "buildings": [],
        "boss_battles": {},
        "last_fish_time": None,
        "banned": False,
        "prestige_level": 0
    }

    await users_collection.update_one({"user_id": user_id}, {"$set": default_user}, upsert=True)
    await callback.message.edit_text("✅ Ваш прогресс был успешно сброшен!")

@router.callback_query(F.data == "cancel_reset")
async def cancel_reset(callback: CallbackQuery):
    await callback.message.edit_text("❌ Сброс отменён.")
