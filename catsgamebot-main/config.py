# config.py
import os
import logging
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Загрузка .env переменных
load_dotenv()

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
LOG_ID = int(os.getenv("LOG_ID", "0"))
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
SUPPORT_CHAT_URL = os.getenv("SUPPORT_CHAT_URL", "")
UPDATES_CHANNEL_URL = os.getenv("UPDATES_CHANNEL_URL", "")

# Проверка обязательных переменных
REQUIRED_VARS = {
    "BOT_TOKEN": BOT_TOKEN,
    "MONGO_URI": MONGO_URI,
    "DB_NAME": DB_NAME,
    "OWNER_ID": OWNER_ID,
}

STARS = "stars"

TOPUP_OPTIONS = {
    "cookies": {"amount": 1, "label": "🍪"},
}

for var, value in REQUIRED_VARS.items():
    if not value:
        raise ValueError(f"❌ Переменная окружения {var} не установлена!")

# Инициализация бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(bot=bot)

# Инициализация MongoDB клиента
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]

# Коллекции
users_collection = db["users"]
referrals_collection = db["referrals"]

# Система рыб с разными ценами и редкостью
FISH_TYPES = {
    "common_fish": {
        "name": "🐟 Обычная рыба",
        "emoji": "🐟",
        "price": 1,
        "rarity": "common",
        "chance": 40,
        "min_level": 1
    },
    "blue_fish": {
        "name": "🐠 Синяя рыба", 
        "emoji": "🐠",
        "price": 3,
        "rarity": "common",
        "chance": 25,
        "min_level": 1
    },
    "puffer_fish": {
        "name": "🐡 Рыба-шар",
        "emoji": "🐡", 
        "price": 8,
        "rarity": "uncommon",
        "chance": 15,
        "min_level": 5
    },
    "tropical_fish": {
        "name": "🐠 Тропическая рыба",
        "emoji": "🐠",
        "price": 12,
        "rarity": "uncommon", 
        "chance": 10,
        "min_level": 10
    },
    "shark": {
        "name": "🦈 Акула",
        "emoji": "🦈",
        "price": 25,
        "rarity": "rare",
        "chance": 5,
        "min_level": 15
    },
    "octopus": {
        "name": "🐙 Осьминог",
        "emoji": "🐙", 
        "price": 35,
        "rarity": "rare",
        "chance": 3,
        "min_level": 20
    },
    "squid": {
        "name": "🦑 Кальмар",
        "emoji": "🦑",
        "price": 45,
        "rarity": "epic",
        "chance": 1.5,
        "min_level": 25
    },
    "whale": {
        "name": "🐋 Кит",
        "emoji": "🐋",
        "price": 100,
        "rarity": "legendary",
        "chance": 0.4,
        "min_level": 35
    },
    "golden_fish": {
        "name": "🟡 Золотая рыба",
        "emoji": "🟡",
        "price": 250,
        "rarity": "mythic",
        "chance": 0.1,
        "min_level": 50
    }
}

# Цвета редкости для отображения
RARITY_COLORS = {
    "common": "⚪",
    "uncommon": "🟢", 
    "rare": "🔵",
    "epic": "🟣",
    "legendary": "🟠",
    "mythic": "🟡"
}

# Названия редкости
RARITY_NAMES = {
    "common": "Обычная",
    "uncommon": "Необычная",
    "rare": "Редкая", 
    "epic": "Эпическая",
    "legendary": "Легендарная",
    "mythic": "Мифическая"
}

BOSS_RESPAWN_TIMES = {
    "pike": 3600,      # Щука - 1 час
    "shark": 7200,     # Белая акула - 2 часа  
    "octopus": 10800,  # Осьминог - 3 часа
    "whale": 14400,    # Кит - 4 часа
    "hunter": 18000,   # Охотник на рыб - 5 часов
    "cthulhu": 21600,  # Ктулху - 6 часов
    "poseidon": 86400  # Посейдон - 24 часа
}

# Кейсы
CASE_TYPES = {
    "can": {"name": "🥫 Банка", "chance": 40},
    "chest": {"name": "📦 Сундук", "chance": 25}, 
    "star_box": {"name": "⭐ Ящик со звёздами", "chance": 15},
    "material_bag": {"name": "🎒 Сумка с материалами", "chance": 10},
    "weapon_box": {"name": "⚔️ Ящик с оружием", "chance": 7},
    "legendary_safe": {"name": "💎 Легендарный сейф", "chance": 3}
}

# События по дням недели
DAILY_EVENTS = {
    0: {"name": "Удачный понедельник", "bonus": "fish_x2"},      # Понедельник
    1: {"name": "Звёздный вторник", "bonus": "stars_x2"},        # Вторник  
    2: {"name": "Торговая среда", "bonus": "sell_x2"},           # Среда
    3: {"name": "Охотничий четверг", "bonus": "boss_drop_x2"},   # Четверг
    4: {"name": "Быстрая пятница", "bonus": "boss_time_x2"},     # Пятница
}

# Материалы
MATERIALS = {
    "wood": {"name": "🪵 Дерево", "emoji": "🪵"},
    "rope": {"name": "🪢 Верёвка", "emoji": "🪢"}, 
    "metal": {"name": "⚙️ Металл", "emoji": "⚙️"},
    "crystal": {"name": "💎 Кристалл", "emoji": "💎"}
}

# Настройки гильдий
GUILD_CREATION_COST = 50000  # Стоимость создания гильдии
GUILD_MAX_LEVEL = 5          # Максимальный уровень гильдии
GUILD_DAILY_TASKS = 3        # Количество ежедневных заданий для гильдии

# Режим тех.работ
MAINTENANCE_MODE = False

