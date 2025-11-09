import asyncio
import logging
from threading import Thread
import aiohttp
from flask import Flask
from config import bot, dp, logger
from modules import start, profile, fishing, inventory, shop, top, bosses, user_stats, cases, promocodes, guide, report, reset, nick, keyboards, clans, clan_chat, upgrade_rod, fishermen
from modules.admin import register_admin_modules
from modules.donate import donate_modules

# ==================== Keep Alive Server ====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8000)

def keep_alive():
    t = Thread(target=run_flask, daemon=True)
    t.start()

# ==================== Auto Ping ====================
async def ping_server():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get("https://mere-amii-kotik130-919e234e.koyeb.app/", timeout=10) as response:
                    if response.status == 200:
                        logger.info("Pinged server to keep alive")
                    else:
                        logger.warning(f"Ping response status: {response.status}")
                await asyncio.sleep(300)
            except Exception as e:
                logger.error(f"Ping error: {e}")
                await asyncio.sleep(60)

# ==================== Main ====================
async def main():
    asyncio.create_task(ping_server())
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(fishing.router)
    dp.include_router(inventory.router)
    dp.include_router(shop.router)
    dp.include_router(top.router)
    dp.include_router(bosses.router)
    dp.include_router(user_stats.router)
    dp.include_router(cases.router)
    dp.include_router(promocodes.router)
    dp.include_router(guide.router)
    dp.include_router(report.router)
    dp.include_router(reset.router)
    dp.include_router(nick.router)
    dp.include_router(keyboards.router)
    dp.include_router(clans.router)
    dp.include_router(clan_chat.router)
    dp.include_router(upgrade_rod.router)
    dp.include_router(fishermen.router)
    register_admin_modules(dp) # автозагрузка модулей для админ панели
    donate_modules(dp) # Автозагрузка функционала для доната
    logger.info("🟢 Бот запущен. Ожидаем команды...")
    try:
        await dp.start_polling(bot)
    except asyncio.CancelledError:
        logger.info("🛑 Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Polling error: {e}")
        await asyncio.sleep(10)

if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен вручную")
    except Exception as e:
        logger.critical(f"Critical error: {e}")
