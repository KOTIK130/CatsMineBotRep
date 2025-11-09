# modules/report.py - Система отчетов об ошибках
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import users_collection, LOG_ID, bot
from datetime import datetime

router = Router(name="report")

class ReportState(StatesGroup):
    waiting_report = State()

@router.message(F.text == "/report")
async def start_report(message: Message, state: FSMContext):
    await message.answer(
        "🐛 <b>Сообщить об ошибке</b>\n\n"
        "Опишите проблему подробно:\n"
        "• Что вы делали?\n"
        "• Что произошло?\n"
        "• Что ожидали?\n\n"
        "Отправьте ваше сообщение:",
        parse_mode="HTML"
    )
    await state.set_state(ReportState.waiting_report)

@router.message(ReportState.waiting_report)
async def handle_report(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "Нет username"
    report_text = message.text
    
    # Сохраняем отчет в базу
    report_data = {
        "user_id": user_id,
        "username": username,
        "report": report_text,
        "created_at": datetime.utcnow(),
        "status": "new"
    }
    
    # Отправляем в лог-канал если настроен
    if LOG_ID:
        try:
            log_message = (
                f"🐛 <b>Новый отчет об ошибке</b>\n\n"
                f"👤 Пользователь: {username} (ID: {user_id})\n"
                f"📝 Сообщение:\n{report_text}\n\n"
                f"🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            )
            await bot.send_message(LOG_ID, log_message, parse_mode="HTML")
        except:
            pass
    
    await message.answer(
        "✅ Спасибо за отчет!\n\n"
        "Ваше сообщение отправлено разработчикам. "
        "Мы рассмотрим его и постараемся исправить проблему.",
        parse_mode="HTML"
    )
    
    await state.clear()
