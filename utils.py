import math
from config import users_collection

def format_value(n: float) -> str:

    suffixes = ['', 'K', 'M', 'B', 'T', 'Qa', 'Qi', 'Sx', 'Sp']

    if n == 0:
        return '0'

    n = float(n)
    abs_n = abs(n)

    # Определяем порядок величины
    order = 0 if abs_n < 1 else int(math.log10(abs_n)) // 3
    order = min(order, len(suffixes) - 1)

    # Масштабируем число
    scaled = n / (10 ** (order * 3))

    # Форматируем вывод
    if scaled == int(scaled):
        return f"{int(scaled)}{suffixes[order]}"
    else:
        return f"{scaled:.2f}".rstrip('0').rstrip('.') + suffixes[order]


def format_progress_bar(percentage: float, length: int = 20) -> str:
    percentage = max(0, min(100, percentage))
    filled = round(percentage / 100 * length)
    empty = length - filled
    return "[" + "▓" * filled + "░" * empty + f"] {percentage:.1f}%"

async def get_user_data(user_id: int) -> dict:
    return await users_collection.find_one({"user_id": user_id})











def format_time(seconds: int) -> str:
    """
    Форматирует время в читаемый формат (HH:MM:SS).
    :param seconds: Количество секунд
    :return: Строка времени
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_multiplier(value: float) -> str:
    """
    Форматирует множитель с фиксированным количеством знаков.
    :param value: Значение множителя
    :return: Строка вида "1.20x"
    """
    return f"{value:.2f}x"

def calculate_upgrade_cost(current_level: int) -> tuple:
    """
    Рассчитывает стоимость улучшения кирки.
    :param current_level: Текущий уровень кирки
    :return: (требуется руды, требуется денег)
    """
    if current_level < 5:
        ore = 10 * (2 ** current_level)
        money = 10 * (2 ** current_level)  # Увеличил базовую стоимость денег
    else:
        # Упрощённая прогрессия после 5 уровня
        level_diff = current_level - 4
        ore = 150 * (4 ** level_diff)      # Вместо 3^n используем 2^n
        money = 200 * (4 ** level_diff)    # Денег требуется в 1.5 раза больше чем руды
    return ore, money

def calculate_dig_amount(pickaxe_level: int, multiplier: float = 1.0) -> tuple:
    """
    Рассчитывает количество добываемой руды.
    :param pickaxe_level: Уровень кирки
    :param multiplier: Множитель добычи
    :return: (базовое значение, значение с множителем)
    """
    base = 2 ** (pickaxe_level - 1)
    boosted = base * multiplier
    return base, boosted
