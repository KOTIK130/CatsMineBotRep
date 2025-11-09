# modules/admin/give_fish.py
from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from decimal import Decimal, InvalidOperation, getcontext
from config import users_collection
from .panel import AdminState, is_admin

getcontext().prec = 28

router = Router()

@router.message(F.text == "🐟 Выдать рыбу")
async def give_fish(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для этой команды.")
        return
    await message.answer("Введите: ID КОЛИЧЕСТВО рыбы\nПример: <code>5045429385 100</code>")
    await state.set_state(AdminState.await_fish)

@router.message(AdminState.await_fish)
async def handle_fish(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError("Неверный формат. Используйте: ID КОЛИЧЕСТВО рыбы")

        uid = int(parts[0])
        amount = Decimal(parts[1]).quantize(Decimal("0.01"))

        if amount <= 0:
            raise ValueError("Количество рыбы должно быть положительным числом.")

        result = await users_collection.update_one(
            {"user_id": uid},
            {"$inc": {"fish": float(amount)}}
        )

        if result.matched_count == 0:
            await message.answer("❌ Пользователь с таким ID не найден.")
        else:
            await message.answer(f"✅ {amount} рыбы выдано пользователю <code>{uid}</code>.")
    except (ValueError, InvalidOperation):
        await message.answer("❌ Неверный формат. Убедитесь, что ID — целое число, а количество рыбы — число.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при выдаче: {e}")
    finally:
        await state.clear()
