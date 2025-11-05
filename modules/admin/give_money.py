# modules/admin/give_money.py
from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from decimal import Decimal, InvalidOperation, getcontext
from config import users_collection
from .panel import AdminState, is_admin

getcontext().prec = 28

router = Router()

@router.message(F.text == "💰 Выдать деньги")
async def give_money(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Введите: ID СУММА\nПример: <code>5045429385 250.50</code>")
    await state.set_state(AdminState.await_money)

@router.message(AdminState.await_money)
async def handle_money(message: types.Message, state: FSMContext):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            raise ValueError("Неверный формат. Используйте: ID СУММА")

        uid = int(parts[0])
        amount = Decimal(parts[1]).quantize(Decimal("0.01"))

        result = await users_collection.update_one(
            {"user_id": uid},
            {"$inc": {"money": float(amount)}}
        )

        if result.matched_count == 0:
            await message.answer("❌ Пользователь с таким ID не найден.")
        else:
            await message.answer(f"✅ {amount}$ выдано пользователю <code>{uid}</code>.")
    except (ValueError, InvalidOperation):
        await message.answer("❌ Неверный формат. Убедитесь, что ID — целое число, а сумма — число.")
    except Exception as e:
        await message.answer(f"❌ Ошибка при выдаче: {e}")
    finally:
        await state.clear()
