import logging
import os
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from typing import Union

# --- Настройка ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("Токен бота не найден в .env файле")
    exit(1)

DATA_FILE = "csgo_data.json"
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- Константы ---
WIN_CHANCE = 60
DRAW_CHANCE = 5
LOSE_CHANCE = 100 - WIN_CHANCE - DRAW_CHANCE

# Файл для хранения промокодов
PROMO_FILE = "promo_codes.json"

# Загрузка промокодов из файла
def load_promo_codes():
    try:
        if os.path.exists(PROMO_FILE):
            with open(PROMO_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Ошибка загрузки промокодов: {e}")
        return {}

# Сохранение промокодов в файл
def save_promo_codes(promo_codes):
    try:
        with open(PROMO_FILE, "w") as f:
            json.dump(promo_codes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения промокодов: {e}")

# Проверка срока действия промокода
def is_promo_valid(promo_info):
    if not promo_info:
        return False
    if promo_info.get("expires"):
        try:
            expire_date = datetime.strptime(promo_info["expires"], "%Y-%m-%d").date()
            return datetime.now().date() <= expire_date
        except:
            return False
    return True

RANKS = {
    0: "Silver 1",
    10: "Silver 2",
    35: "Silver 3",
    50: "Silver 4",
    100: "Gold Nova 1",
    150: "Gold Nova 2",
    200: "Gold Nova 3",
    250: "Gold Nova 4",
    300: "Master Guardian 1",
    350: "Master Guardian 2",
    400: "DMG",
    450: "LE",
    500: "LEM",
    600: "Supreme",
    750: "Global Elite",
    1000: "Faceit 1",
    1250: "Faceit 2",
    1500: "Faceit 3",
    1750: "Faceit 4",
    2000: "Faceit 5",
    2250: "Faceit 6",
    2500: "Faceit 7",
    2700: "Faceit 8",
    3000: "Faceit 9",
    3250: "Faceit 10",
    5000: "Challenger 💎"
}

WIN_PHRASES = {
    "Terrorists": [
        "Bomb has been planted! 💣",
        "T wins! Rush B успешен! 🏃",
        "Изи пизи лимон сквизи! 🍋",
        "Терры победили! GG EZ!",
        "ГГ в чатик! Хорошая игра! ✌️",
        "Командная работа: я командовал — вы работали!",
        "Изи фо Энс, Энс, Энс Дэнс пУтэт аппербелт ПУтэт аппербелт"
    ],
    "Counter-Terrorists": [
        "Bomb defused! 🛡️",
        "CT win! Mission accomplished! ✅",
        "Спецназ рулит! Терры что с лицом ?👮",
        "GG, теры в шоке от этой прикормки",
        "флэш, флэш бадэнг, флэш бадэнг э дэнс Флэш, флэш бадэнг, бэнг э дэнг э дэнс", 
        "Позвоните в МЧС — я только что сжёг пятерых!"
    ]
}

LOSE_PHRASES = [
    "Ты проиграл... лаги, конечно! 🌐",
    "слышны только удары по столу",
    "ОКАК",
    "НУ как так? Была одна победа до повышения🔌",
    "Это стратегическое отступление! 🏃",
    "я такой лоутаб",
    "Братва, зато по фану!",
    "GG, я иду плакать."
]

DRAW_PHRASES = [
    "Ничья! Кто-то доволен?",
    "30-30 - классика! 🎭",
    "Ну почти... почти... 🤏",
    "Оба молодцы  🤝",
    "Технически — мы не проиграли!",
    "Фигня, давай по новой."
]

PROMO_CODES = {
    "CSGO2025": {
        "points": 15,
        "max_uses": 3500,
        "used": 0,
        "used_by": []
    },
    "HEADSHOT": {
        "points": 10, 
        "max_uses": 1000,
        "used": 0,
        "used_by": []
    }
}

# --- Клавиатуры ---
def get_team_keyboard():
    return InlineKeyboardMarkup().row(
        InlineKeyboardButton("💣 Террористы", callback_data="team_t"),
        InlineKeyboardButton("🛡️ Спецназ", callback_data="team_ct")
    )

def get_main_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True).row(
        KeyboardButton("🎮 Сыграть матч"),
        KeyboardButton("📊 Моя статистика")
    ).row(
        KeyboardButton("🏆 Топ игроков"),
        KeyboardButton("❓ Помощь")
    )

def get_choice_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True).row(
        KeyboardButton("💣 Террористы"),
        KeyboardButton("🛡️ Спецназ"),
        KeyboardButton("🔙 Назад")
    )

# --- Функции работы с данными ---
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Ошибка загрузки данных: {e}")
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных: {e}")

def get_next_rank(points):
    sorted_ranks = sorted(RANKS.items())
    for i, (threshold, rank) in enumerate(sorted_ranks):
        if points < threshold:
            prev_threshold = sorted_ranks[i - 1][0] if i > 0 else 0
            prev_rank = sorted_ranks[i - 1][1] if i > 0 else "Silver 1"
            return prev_rank, threshold - points
    return sorted_ranks[-1][1], 0

def format_timedelta(delta: timedelta) -> str:
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    return f"{hours}ч {minutes}м"

def save_promo_uses():
    data = load_data()
    data["promo_uses"] = PROMO_CODES
    save_data(data)

def load_promo_uses():
    data = load_data()
    if "promo_uses" in data:
        for code in PROMO_CODES:
            if code in data["promo_uses"]:
                PROMO_CODES[code]["used"] = data["promo_uses"][code]["used"]
                PROMO_CODES[code]["used_by"] = data["promo_uses"][code].get("used_by", [])

# --- Обработчики ---
async def is_group_chat(message: Union[types.Message, types.CallbackQuery]):
    if isinstance(message, types.CallbackQuery):
        message = message.message
    return message.chat.type in ("group", "supergroup")

@dp.message_handler(commands=['start', 'help'])
async def start(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("🤖 Этот бот работает только в группах!\n\n"
                           "Добавьте меня в группу, чтобы играть в CS:GO матчи.\n\n"
                           "По всем предложениям/рекламе: @George321123")
        return
    await message.answer("🎮 <b>CS:GO Match Bot</b>", reply_markup=get_main_menu(), parse_mode="HTML")

@dp.message_handler(commands=['promo'])
async def promo_handler(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("ℹ️ Промокоды активируются только в группах!")
        return

    try:
        promo_code = message.text.split()[1].upper()
    except IndexError:
        await message.reply("❌ Укажите промокод: /promo КОД")
        return

    if promo_code not in PROMO_CODES:
        await message.reply("❌ Неверный промокод")
        return

    user_id = str(message.from_user.id)
    
    if user_id in PROMO_CODES[promo_code]["used_by"]:
        await message.reply("⚠️ Вы уже использовали этот промокод!")
        return

    if PROMO_CODES[promo_code]["used"] >= PROMO_CODES[promo_code]["max_uses"]:
        await message.reply("⚠️ Лимит активаций исчерпан")
        return

    chat_id = str(message.chat.id)
    bonus = PROMO_CODES[promo_code]["points"]
    
    data = load_data()
    if chat_id not in data:
        data[chat_id] = {"players": {}}
    if user_id not in data[chat_id]["players"]:
        data[chat_id]["players"][user_id] = {"points": 0, "wins": 0}

    data[chat_id]["players"][user_id]["points"] += bonus
    PROMO_CODES[promo_code]["used"] += 1
    PROMO_CODES[promo_code]["used_by"].append(user_id)
    
    save_data(data)
    save_promo_uses()
    
    await message.reply(
        f"🎉 Промокод активирован!\n"
        f"+{bonus} очков\n"
        f"Осталось активаций: {PROMO_CODES[promo_code]['max_uses'] - PROMO_CODES[promo_code]['used']}\n"
        f"⚠️ Вы больше не сможете использовать этот промокод!"
    )

@dp.message_handler(commands=['t'])
async def choose_t(message: types.Message):
    if not await is_group_chat(message):
        return
    await process_team_choice(message, "Terrorists")

@dp.message_handler(commands=['ct'])
async def choose_ct(message: types.Message):
    if not await is_group_chat(message):
        return
    await process_team_choice(message, "Counter-Terrorists")

@dp.message_handler(lambda m: m.text == "🎮 Сыграть матч")
async def play_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    await message.answer("Выберите команду:", reply_markup=get_choice_menu())

@dp.message_handler(lambda m: m.text in ["💣 Террористы", "🛡️ Спецназ"])
async def team_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    team = "Terrorists" if message.text == "💣 Террористы" else "Counter-Terrorists"
    await process_team_choice(message, team)

@dp.message_handler(lambda m: m.text == "🔙 Назад")
async def back_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    await message.answer("Главное меню:", reply_markup=get_main_menu())

@dp.message_handler(commands=['stats'])
@dp.message_handler(lambda m: m.text == "📊 Моя статистика")
async def show_stats(message: types.Message):
    if not await is_group_chat(message):
        return 
    
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if chat_id not in data or user_id not in data[chat_id].get("players", {}):
        await message.reply("Вы еще не играли в этом чате!", reply_markup=get_main_menu())
        return
    
    player = data[chat_id]["players"][user_id]
    points = player.get("points", 0)
    rank, points_needed = get_next_rank(points)
    
    last_play = player.get("last_play")
    if last_play:
        try:
            last_play_dt = datetime.fromisoformat(last_play)
            time_left = timedelta(hours=12) - (datetime.now() - last_play_dt)
            if time_left.total_seconds() > 0:
                cooldown = f"⏳ До следующей игры: {format_timedelta(time_left)}"
            else:
                cooldown = "✅ Можно играть сейчас"
        except:
            cooldown = "⏳ Время кулдауна неизвестно"
    else:
        cooldown = "✅ Можно играть сейчас"
    
    await message.reply(
        f"📊 <b>Ваша статистика:</b>\n\n"
        f"🏅 Текущий ранг: {rank}\n"
        f"⭐ Очки: {points}\n"
        f"📈 До следующего ранга: {points_needed} очков\n"
        f"🎯 Побед: {player.get('wins', 0)}\n"
        f"{cooldown}",
        reply_markup=get_main_menu(),
        parse_mode=types.ParseMode.HTML
    )

@dp.message_handler(commands=['help'])
@dp.message_handler(lambda m: m.text == "❓ Помощь")
async def help_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    
    help_text = (
        "🎮 <b>CS:GO Match Bot - Помощь</b>\n"
        "<b>👉 Поддержи проект донатом-https://boosty.to/rankgrinder_bot</b>\n\n"
        "<b>Основные команды:</b>\n"
        "• /t или кнопка 💣 Террористы - играть за террористов\n"
        "• /ct или кнопка 🛡️ Спецназ - играть за спецназ\n"
        "• /stats или кнопка 📊 Моя статистика - ваша статистика\n"
        "• /promo и промокод- ввод промокода\n"
        "• /top или кнопка 🏆 Топ игроков - топ игроков чата\n\n"
        "<b>Как играть:</b>\n"
        "1. Выберите команду (Террористы/Спецназ)\n"
        "2. Бот определит результат матча\n"
        "3. Получайте очки и повышайте ранг\n"
        "4. Играть можно 1 раз в 12 часа в каждом чате\n\n"
        "<b>Система рангов:</b>\n"
        "• Ранги от Silver 1 до Challenger💎\n"
        "• За победы получаете очки (1-10 за победу)\n"
        "• За поражения теряете очки (1-10 за поражение)\n"
        "• Ничья не изменяет количество очков"
    )
    
    await message.answer(
        help_text,
        reply_markup=get_main_menu(),
        parse_mode=types.ParseMode.HTML
    )

@dp.message_handler(commands=['top'])
@dp.message_handler(lambda m: m.text == "🏆 Топ игроков")
async def show_top(message: types.Message):
    if not await is_group_chat(message):
        return
    
    data = load_data()
    chat_id = str(message.chat.id)
    
    if chat_id not in data or not data[chat_id].get("players"):
        await message.reply("В этом чате еще никто не играл!", reply_markup=get_main_menu())
        return
    
    players = sorted(
        data[chat_id]["players"].items(),
        key=lambda x: (x[1].get("points", 0), x[1].get("wins", 0)),
        reverse=True
    )[:10]
    
    team = random.choice(["NAVI", "Virtus pro", "Gambit", "Faze"])
    top_text = f"🏆 {team} | <b>Топ игроков:</b>\n\n"
    
    for i, (user_id, stats) in enumerate(players, 1):
        try:
            user = await bot.get_chat_member(chat_id, int(user_id))
            name = f"{user.user.username}" if user.user.username else user.user.first_name
        except Exception as e:
            logging.error(f"Ошибка получения пользователя {user_id}: {e}")
            name = stats.get("username", f"Игрок {user_id[-4:]}")
        
        points = stats.get("points", 0)
        wins = stats.get("wins", 0)
        rank = get_next_rank(points)[0]
        top_text += f"{i}. {name} - {points} очков | {wins} побед (ранг: {rank})\n"
    
    await message.reply(top_text, reply_markup=get_main_menu(), parse_mode=types.ParseMode.HTML)

async def process_team_choice(message: types.Message, team: str):
    if not await is_group_chat(message):
        return
    
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    
    if chat_id not in data:
        data[chat_id] = {"players": {}}
    if user_id not in data[chat_id]["players"]:
        data[chat_id]["players"][user_id] = {
            "wins": 0,
            "points": 0,
            "last_play": None,
        }
    
    player = data[chat_id]["players"][user_id]
    player["username"] = message.from_user.username or message.from_user.first_name
    
    if player.get("last_play"):
        try:
            last_play = datetime.fromisoformat(player["last_play"])
            time_left = timedelta(hours=12) - (datetime.now() - last_play)
            if time_left.total_seconds() > 0:
                await message.reply(
                    f"⏳ До следующей игры осталось: {format_timedelta(time_left)}",
                    reply_markup=get_main_menu()
                )
                return
        except Exception as e:
            logging.error(f"Ошибка проверки кулдауна: {e}")
    
    result = random.choices(
        ["win", "lose", "draw"],
        weights=[WIN_CHANCE, LOSE_CHANCE, DRAW_CHANCE],
        k=1
    )[0]
    
    if result == "win":
        points = random.randint(1, 10)
        player["points"] += points
        player["wins"] += 1
        phrase = random.choice(WIN_PHRASES[team])
        outcome = f"{phrase}\nПобеда! +{points} очков 🏆"
    elif result == "lose":
        points = random.randint(1, 10)
        player["points"] = max(0, player["points"] - points)
        phrase = random.choice(LOSE_PHRASES)
        outcome = f"{phrase}\nПоражение... -{points} очков 💀"
    else:
        phrase = random.choice(DRAW_PHRASES)
        outcome = f"{phrase}\nНичья! Очки не изменились ➖"
    
    player["last_play"] = datetime.now().isoformat()
    save_data(data)
    
    rank, points_needed = get_next_rank(player["points"])
    
    await message.reply(
        f"{outcome}\n\n"
        f"🏅 Текущий ранг: {rank}\n"
        f"⭐ Очки: {player['points']}\n"
        f"📈 До следующего ранга: {points_needed} очков\n"
        f"🎯 Побед: {player['wins']}",
        reply_markup=get_main_menu()
    )

@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def welcome_new_chat(message: types.Message):
    for new_member in message.new_chat_members:
        if new_member.id == bot.id:
            welcome_text = (
                "🎮 <b>CS:GO Match Bot</b>\n\n"
                "<b>Основные команды:</b>\n"
                "• /t или кнопка 💣 Террористы - играть за террористов\n"
                "• /ct или кнопка 🛡️ Спецназ - играть за спецназ\n"
                "• /stats или кнопка 📊 Моя статистика - ваша статистика\n"
                "• /top или кнопка 🏆 Топ игроков - топ игроков чата\n\n"
                "• /promo и промокод- ввод промокода\n"
                "<b>Как играть:</b>\n"
                "1. Выберите команду (Террористы/Спецназ)\n"
                "2. Бот определит результат матча\n"
                "3. Получайте очки и повышайте ранг\n"
                "4. Играть можно 1 раз в 12 часа в каждом чате\n\n"
                "<b>Система рангов:</b>\n"
                "• Ранги от Silver 1 до Challenger💎\n"
                "• За победы получаете очки (1-10 за победу)\n"
                "• За поражения теряете очки (1-10 за поражение)\n"
                "• Ничья не изменяет количество очков"
            )
            
            await message.reply(
                welcome_text,
                reply_markup=get_main_menu(),
                parse_mode=types.ParseMode.HTML
            )

# Инициализация при старте
load_promo_uses()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)