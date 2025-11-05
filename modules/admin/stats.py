from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from config import users_collection
from utils import format_value
from .panel import AdminState, is_admin

router = Router()

@router.message(F.text == "📊 Получить статистику")
async def get_stats(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите ID игрока:")
    await state.set_state(AdminState.await_stats)

@router.message(AdminState.await_stats)
async def handle_stats(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text)
        user = await users_collection.find_one({"user_id": uid})
        if not user:
            await message.answer("Игрок не найден")
            return
        text = (
            f"📌 Статистика рыбака {uid}\n"
            f"├ Уровень удочки: {user.get('rod_level', 1)}\n"
            f"├ Престиж: {user.get('prestige_level', 0)}\n"
            f"├ Деньги: {format_value(user.get('money', 0))}\n"
            f"├ Рыба: {format_value(user.get('fish', 0))}\n"
            f"├ Всего поймано: {format_value(user.get('total_fish_caught', 0))}\n"
            f"├ Морские звёзды: {user.get('sea_stars', 0)}\n"
            f"├ Печеньки: {user.get('cookies', 0)}\n"
            f"└ Множитель рыбы: {user.get('fish_multiplier', 1.0):.1f}x"
        )
        await message.answer(text)
    finally:
        await state.clear()
