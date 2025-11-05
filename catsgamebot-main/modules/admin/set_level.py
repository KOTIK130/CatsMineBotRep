from aiogram import Router, types
from aiogram import F
from aiogram.fsm.context import FSMContext
from config import users_collection
from .panel import AdminState, is_admin

router = Router()

@router.message(F.text == "📈 Установить уровень")
async def set_level(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    await message.answer(
        "Введите: ID УРОВЕНЬ (от 1 до 60)\n"
        "Пример: `5045429385 10`", parse_mode="Markdown"
    )
    await state.set_state(AdminState.await_level)

@router.message(AdminState.await_level)
async def handle_level(message: types.Message, state: FSMContext):
    try:
        uid, level = map(int, message.text.split())
        
        if level < 1 or level > 60:
            await message.answer("❌ Уровень удочки должен быть от 1 до 60.")
            return
        
        result = await users_collection.update_one(
            {"user_id": uid},
            {"$set": {"rod_level": level}}
        )

        if result.modified_count > 0:
            await message.answer(f"✅ Установлен уровень удочки {level} игроку {uid}")
        else:
            await message.answer(f"❌ Игрок с ID {uid} не найден.")
    
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный формат: ID УРОВЕНЬ (например, 5045429385 10).")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.clear()
