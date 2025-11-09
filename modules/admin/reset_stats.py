from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from config import users_collection
from .panel import AdminState, is_admin

router = Router()

@router.message(F.text == "♻️ Сбросить статистику")
async def reset_stats(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите ID игрока:")
    await state.set_state(AdminState.await_reset)

@router.message(AdminState.await_reset)
async def handle_reset(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text)
        await users_collection.update_one(
            {"user_id": uid},
            {"$set": {
                "fish": 0, 
                "money": 0, 
                "total_fish_caught": 0, 
                "rod_level": 1,
                "sea_stars": 0,
                "prestige_level": 0,
                "fish_multiplier": 1.0,
                "star_chance": 5.0,
                "luck_x2": 10.0
            }}
        )
        await message.answer(f"♻️ Статистика рыбака {uid} сброшена")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()
