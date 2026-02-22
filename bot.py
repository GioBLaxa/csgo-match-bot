import logging
import os
import random
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import Union
import asyncio

# --- Настройка ---
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("Токен бота не найден в .env файле")
    exit(1)

DATA_FILE = "csgo_data.json"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Константы ---
WIN_CHANCE = 60
DRAW_CHANCE = 5
LOSE_CHANCE = 100 - WIN_CHANCE - DRAW_CHANCE

PROMO_FILE = "promo_codes.json"

SKINS = {
    "AK-47 | Красная линия": {"rarity": "uncommon", "price": 126, "image": "https://i.postimg.cc/FzDYdG7v/Chat-GPT-Image-28-2025-20-43-48.png"},
    "AK-47 | Прямо с завода": {"rarity": "uncommon", "price": 100, "image": "https://i.postimg.cc/63X4KnJr/Chat-GPT-Image-29-2025-11-45-01.png"},
    "AWP | Африканская сетка": {"rarity": "common", "price": 70, "image": "https://i.postimg.cc/bvkdHqs3/Chat-GPT-Image-28-2025-20-44-33.png"},
    "P250 | Муертос": {"rarity": "common", "price": 8, "image": "https://i.postimg.cc/xd40NCGX/image.png"},
    "AK47 | 'Элитное снарежение": {"rarity": "rare", "price": 150, "image": "https://i.postimg.cc/bYZCpvFZ/image.png"},
    "AK-47 | Африканская сетка": {"rarity": "common", "price": 34, "image": "https://postimg.cc/5QdqF328"},
    "AWP | Сгорающая прибыль": {"rarity": "rare", "price": 255, "image": "https://i.postimg.cc/T1qw80rm/photo-2025-05-28-20-24-09.jpg"},
    "Desert Eagle | Огненная буря": {"rarity": "rare", "price": 220, "image": "https://i.postimg.cc/Nf9pzkdL/Chat-GPT-Image-29-2025-10-49-06.png"},
    "UMP-45 | Blaze": {"rarity": "uncommon", "price": 90, "image": "https://i.postimg.cc/0ymxPmyy/3c20f497-19aa-440b-9364-bf88fba90cac.png"},
    "Нож | Бабочка | Тигриный клык": {"rarity": "legendary", "price": 500, "image": "https://i.postimg.cc/dVLXYTwS/Chat-GPT-Image-29-2025-11-29-32.png"},
    "Перчатки | Леопардовые": {"rarity": "legendary", "price": 600, "image": "https://i.postimg.cc/RVj5sRzZ/1e88b865-4cb1-400f-b0a6-54a80adf5637.png"},
    "Нож | Керамбит | Изыск": {"rarity": "legendary", "price": 650, "image": "https://i.postimg.cc/02tdPWN9/87321e5c-526d-47e2-a4a0-4174d3a03a8e.png"},
    "AWP | История о пьяном драконе": {"rarity": "rare", "price": 200, "image": "https://i.postimg.cc/j2c26F12/f268e53d-0d81-47d4-af27-e790252430e7.png"},
    "Desert Eagle | Самородок": {"rarity": "rare", "price": 180, "image": "https://i.postimg.cc/8c0JQWPb/Chat-GPT-Image-29-2025-11-03-56.png"}
}

CASES = {
    "weapon_case": {
        "name": "Оружейный кейс",
        "price": 80,
        "image": "https://i.postimg.cc/85711Kw6/Chat-GPT-Image-28-2025-10-49-09.png",
        "contains": [
            "AK-47 | Прямо с завода",
            "AWP | Африканская сетка",
            "P250 | Муертос",
            "AK47 | 'Элитное снарежение",
            "AK-47 | Африканская сетка"
        ]
    },
    "fire_case": {
        "name": "Огненный кейс",
        "price": 150,
        "image": "https://i.postimg.cc/7ZPrHtZZ/Chat-GPT-Image-28-2025-10-51-00.png",
        "contains": [
            "AWP | Сгорающая прибыль",
            "Desert Eagle | Огненная буря",
            "AK-47 | Красная линия",
            "UMP-45 | Blaze",
            "P250 | Муертос"
        ]
    },
    "premium_case": {
        "name": "Буржуйский кейс",
        "price": 350,
        "image": "https://i.postimg.cc/rsnhYwX6/Chat-GPT-Image-28-2025-18-28-21.png",
        "contains": [
            "Нож | Бабочка | Тигриный клык",
            "Перчатки | Леопардовые",
            "Нож | Керамбит | Изыск",
            "AWP | История о пьяном драконе",
            "Desert Eagle | Самородок",
            "AK-47 | Прямо с завода"
        ]
    }
}

RARITY_PROBABILITIES = {
    "common": 45,
    "uncommon": 30,
    "rare": 20,
    "legendary": 5
}

for case_id, case_data in CASES.items():
    for skin in case_data["contains"]:
        if skin not in SKINS:
            logging.error(f"❌ В кейсе '{case_data['name']}' указан несуществующий скин: '{skin}'")

def load_promo_codes():
    try:
        if os.path.exists(PROMO_FILE):
            with open(PROMO_FILE, "r") as f:
                return json.load(f)
        return {}
    except Exception as e:
        logging.error(f"Ошибка загрузки промокодов: {e}")
        return {}

def save_promo_codes(promo_codes):
    try:
        with open(PROMO_FILE, "w") as f:
            json.dump(promo_codes, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения промокодов: {e}")

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
    5: "Silver 2",
    15: "Silver 3",
    25: "Silver 4",
    35: "Gold Nova 1",
    45: "Gold Nova 2",
    60: "Gold Nova 3",
    75: "Gold Nova 4",
    90: "Master Guardian 1",
    110: "Master Guardian 2",
    130: "DMG",
    150: "LE",
    180: "LEM",
    210: "Supreme",
    230: "Global Elite",
    260: "Faceit 1",
    290: "Faceit 2",
    310: "Faceit 3",
    350: "Faceit 4",
    400: "Faceit 5",
    450: "Faceit 6",
    500: "Faceit 7",
    600: "Faceit 8",
    800: "Faceit 9",
    1000: "Faceit 10",
    2500: "Challenger 💎"
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
        "points": 60,
        "max_uses": 1500,
        "used": 0,
        "used_by": []
    },
    "HEADSHOT": {
        "points": 55,
        "max_uses": 350,
        "used": 0,
        "used_by": []
    },
    "SASAPIDR": {
        "points": 520,
        "max_uses": 1,
        "used": 0,
        "used_by": []
    },
    "HENDAYGOVNO": {
        "points": 500,
        "max_uses": 10,
        "used": 0,
        "used_by": []
    },
    "TURKFUNK": {
        "points": 500,
        "max_uses": 10,
        "used": 0,
        "used_by": []
    }
}

# --- Вспомогательная функция удаления сообщений ---
async def safe_delete(chat_id, message_id):
    """Удаляет сообщение, игнорируя ошибки если уже удалено"""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

# --- Клавиатуры ---
def get_team_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💣 Террористы", callback_data="team_t"),
            InlineKeyboardButton(text="🛡️ Спецназ", callback_data="team_ct")
        ]
    ])

def get_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎮 Сыграть матч"), KeyboardButton(text="📊 Моя статистика")],
            [KeyboardButton(text="🏆 Топ игроков"), KeyboardButton(text="🎁 Открыть кейс"), KeyboardButton(text="❓ Помощь")]
        ],
        resize_keyboard=True
    )

def get_choice_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💣 Террористы"), KeyboardButton(text="🛡️ Спецназ"), KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True
    )

def get_cases_menu():
    buttons = []
    for case_id, case_data in CASES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{case_data['name']} - {case_data['price']} очков",
            callback_data=f"case_{case_id}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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

def get_next_rank(wins):
    sorted_ranks = sorted(RANKS.items())
    for i, (threshold, rank) in enumerate(sorted_ranks):
        if wins < threshold:
            prev_rank = sorted_ranks[i-1][1] if i > 0 else "Silver 1"
            return prev_rank, threshold - wins
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

@dp.message(Command('start'))
async def start(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("🤖 Этот бот работает только в группах!\n\n"
                           "Добавьте меня в группу, чтобы играть в CS:GO матчи.\n\n"
                           "По всем предложениям/рекламе: @George321123")
        return
    await message.answer("🎮 <b>CS:GO Match Bot</b>", reply_markup=get_main_menu(), parse_mode="HTML")

@dp.message(Command('help'))
async def help_command(message: types.Message):
    await help_handler(message)

@dp.message(Command('promo'))
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

@dp.message(Command('t'))
async def choose_t(message: types.Message):
    if not await is_group_chat(message):
        return
    await process_team_choice(message, "Terrorists")

@dp.message(Command('ct'))
async def choose_ct(message: types.Message):
    if not await is_group_chat(message):
        return
    await process_team_choice(message, "Counter-Terrorists")

@dp.message(F.text == "🎮 Сыграть матч")
async def play_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    # Удаляем сообщение пользователя
    await safe_delete(message.chat.id, message.message_id)
    await message.answer("Выберите команду:", reply_markup=get_choice_menu())

@dp.message(F.text.in_(["💣 Террористы", "🛡️ Спецназ"]))
async def team_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    # Удаляем сообщение пользователя с выбором команды
    await safe_delete(message.chat.id, message.message_id)
    team = "Terrorists" if message.text == "💣 Террористы" else "Counter-Terrorists"
    await process_team_choice(message, team)

@dp.message(F.text == "🔙 Назад")
async def back_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    # Удаляем сообщение пользователя
    await safe_delete(message.chat.id, message.message_id)
    await message.answer("Главное меню:", reply_markup=get_main_menu())

@dp.message(Command('stats'))
@dp.message(F.text == "📊 Моя статистика")
async def show_stats(message: types.Message):
    if not await is_group_chat(message):
        return
    # Удаляем сообщение пользователя
    await safe_delete(message.chat.id, message.message_id)

    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    if chat_id not in data or user_id not in data[chat_id].get("players", {}):
        await message.answer("Вы еще не играли в этом чате!", reply_markup=get_main_menu())
        return

    player = data[chat_id]["players"][user_id]
    wins = player.get("wins", 0)
    points = player.get("points", 0)
    rank, wins_needed = get_next_rank(wins)

    last_play = player.get("last_play")
    if last_play:
        try:
            last_play_dt = datetime.fromisoformat(last_play)
            time_left = timedelta(hours=10) - (datetime.now() - last_play_dt)
            if time_left.total_seconds() > 0:
                cooldown = f"⏳ До следующей игры: {format_timedelta(time_left)}"
            else:
                cooldown = "✅ Можно играть сейчас"
        except:
            cooldown = "⏳ Время кулдауна неизвестно"
    else:
        cooldown = "✅ Можно играть сейчас"

    # Статистика остаётся навсегда
    await message.answer(
        f"📊 <b>Ваша статистика:</b>\n\n"
        f"🏅 Текущий ранг: {rank}\n"
        f"⭐ Очки: {points}\n"
        f"📈 До следующего ранга: {wins_needed} побед\n"
        f"🎯 Побед: {wins}\n"
        f"{cooldown}",
        reply_markup=get_main_menu(),
        parse_mode="HTML"
    )

@dp.message(F.text == "❓ Помощь")
async def help_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    # Удаляем сообщение пользователя
    await safe_delete(message.chat.id, message.message_id)

    help_text = (
        "🎮 <b>CS:GO Match Bot - Помощь</b>\n"
        "<b>👉 Поддержи проект донатом-https://boosty.to/rankgrinder_bot</b>\n\n"
        "<b>Основные команды:</b>\n"
        "• /t или кнопка 💣 Террористы - играть за террористов\n"
        "• /ct или кнопка 🛡️ Спецназ - играть за спецназ\n"
        "• /stats или кнопка 📊 Моя статистика - ваша статистика\n"
        "• /promo и промокод- ввод промокода\n"
        "• /top или кнопка 🏆 Топ игроков - топ игроков чата\n"
        "• /open или кнопка 🎁 Открыть кейс - открыть кейс со скинами\n\n"
        "<b>Как играть:</b>\n"
        "1. Выберите команду (Террористы/Спецназ)\n"
        "2. Бот определит результат матча\n"
        "3. Получайте очки и повышайте ранг\n"
        "4. Играть можно 1 раз в 10 часов в каждом чате\n\n"
        "<b>Система рангов:</b>\n"
        "• Ранги от Silver 1 до Challenger💎\n"
        "• За победы получаете очки (1-15 за победу)\n"
        "• За поражения теряете очки (1-10 за поражение)\n"
        "• Ничья не изменяет количество очков\n\n"
        "<b>Система кейсов:</b>\n"
        "• Можно открывать кейсы за очки\n"
        "• Чем дороже кейс - тем лучше скины\n"
        "• Редкие скины выпадают редко"
    )

    # Помощь удаляется через 30 секунд
    sent = await message.answer(help_text, reply_markup=get_main_menu(), parse_mode="HTML")
    await asyncio.sleep(30)
    await safe_delete(message.chat.id, sent.message_id)

@dp.message(Command('top'))
@dp.message(F.text == "🏆 Топ игроков")
async def show_top(message: types.Message):
    if not await is_group_chat(message):
        return
    # Удаляем сообщение пользователя
    await safe_delete(message.chat.id, message.message_id)

    data = load_data()
    chat_id = str(message.chat.id)

    if chat_id not in data or not data[chat_id].get("players"):
        await message.answer("В этом чате еще никто не играл!", reply_markup=get_main_menu())
        return

    players = sorted(
        data[chat_id]["players"].items(),
        key=lambda x: (x[1].get("wins", 0), x[1].get("points", 0)),
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
        rank = get_next_rank(wins)[0]
        top_text += f"{i}. {name} - {points} очков | {wins} побед (ранг: {rank})\n"

    # Топ остаётся навсегда
    await message.answer(top_text, reply_markup=get_main_menu(), parse_mode="HTML")

@dp.message(Command('open'))
@dp.message(F.text == "🎁 Открыть кейс")
async def open_case_handler(message: types.Message):
    if not await is_group_chat(message):
        return
    # Удаляем сообщение пользователя
    await safe_delete(message.chat.id, message.message_id)

    await message.answer(
        "🎁 <b>Выберите кейс для открытия:</b>",
        reply_markup=get_cases_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data.startswith('case_'))
async def process_case_callback(callback_query: types.CallbackQuery):
    case_id = callback_query.data[5:]
    if case_id not in CASES:
        await callback_query.answer("❌ Такого кейса не существует")
        return

    case_data = CASES[case_id]
    user_id = str(callback_query.from_user.id)
    chat_id = str(callback_query.message.chat.id)

    data = load_data()
    if chat_id not in data or user_id not in data[chat_id]["players"]:
        await callback_query.answer("❌ Вы еще не играли в этом чате!")
        return

    player_points = data[chat_id]["players"][user_id].get("points", 0)
    if player_points < case_data["price"]:
        await callback_query.answer(f"❌ Недостаточно очков! Нужно {case_data['price']}")
        return

    # Удаляем сообщение "Выберите кейс" с кнопками
    await safe_delete(chat_id, callback_query.message.message_id)

    # Отправляем фото кейса с кнопкой "Открыть"
    await bot.send_photo(
        chat_id=callback_query.message.chat.id,
        photo=case_data["image"],
        caption=f"🎁 Вы выбрали: {case_data['name']}\n"
                f"💳 Стоимость: {case_data['price']} очков\n\n"
                f"Нажмите кнопку ниже, чтобы открыть кейс!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔓 Открыть кейс", callback_data=f"open_{case_id}")]
        ])
    )
    await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith('open_'))
async def process_open_case(callback_query: types.CallbackQuery):
    case_id = callback_query.data[5:]
    if case_id not in CASES:
        await callback_query.answer("❌ Такого кейса не существует")
        return

    case_data = CASES[case_id]
    user_id = str(callback_query.from_user.id)
    chat_id = str(callback_query.message.chat.id)

    data = load_data()
    if chat_id not in data or user_id not in data[chat_id]["players"]:
        await callback_query.answer("❌ Вы еще не играли в этом чате!")
        return

    player_points = data[chat_id]["players"][user_id].get("points", 0)
    if player_points < case_data["price"]:
        await callback_query.answer(f"❌ Недостаточно очков! Нужно {case_data['price']}")
        return

    # Удаляем фото кейса с кнопкой "Открыть"
    await safe_delete(chat_id, callback_query.message.message_id)

    # Вычитаем стоимость кейса
    data[chat_id]["players"][user_id]["points"] -= case_data["price"]
    save_data(data)

    # Выбираем скин с учетом редкости
    possible_skins = case_data["contains"]
    skins_with_rarity = []

    for skin in possible_skins:
        try:
            skin_data = SKINS[skin]
            skins_with_rarity.append((skin, skin_data["rarity"]))
        except KeyError:
            logging.error(f"Скин '{skin}' не найден в SKINS!")
            continue

    if not skins_with_rarity:
        await callback_query.answer("❌ Ошибка: нет доступных скинов в кейсе")
        return

    weights = [RARITY_PROBABILITIES[rarity] for _, rarity in skins_with_rarity]
    selected_skin = random.choices(
        population=[skin for skin, _ in skins_with_rarity],
        weights=weights,
        k=1
    )[0]

    skin_data = SKINS[selected_skin]

    # Добавляем стоимость скина к балансу
    data[chat_id]["players"][user_id]["points"] += skin_data["price"]
    save_data(data)

    # Отправляем результат дропа — НЕ удаляется!
    try:
        await bot.send_photo(
            chat_id=callback_query.message.chat.id,
            photo=skin_data["image"],
            caption=f"🎉 Поздравляем! Вы получили:\n\n"
                    f"🔫 <b>{selected_skin}</b>\n"
                    f"🏷 Редкость: {skin_data['rarity']}\n"
                    f"💵 Стоимость: {skin_data['price']} очков\n\n"
                    f"💳 Потрачено: {case_data['price']} очков\n"
                    f"💰 Баланс: {data[chat_id]['players'][user_id]['points']} очков",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Ошибка отправки изображения: {e}")
        await bot.send_message(
            chat_id=callback_query.message.chat.id,
            text=f"🎉 Поздравляем! Вы получили:\n\n"
                 f"🔫 <b>{selected_skin}</b>\n"
                 f"🏷 Редкость: {skin_data['rarity']}\n"
                 f"💵 Стоимость: {skin_data['price']} очков\n\n"
                 f"💳 Потрачено: {case_data['price']} очков\n"
                 f"💰 Баланс: {data[chat_id]['players'][user_id]['points']} очков",
            parse_mode="HTML"
        )

    await callback_query.answer()

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main_menu(callback_query: types.CallbackQuery):
    # Удаляем сообщение с кнопками кейсов
    await safe_delete(callback_query.message.chat.id, callback_query.message.message_id)
    await callback_query.message.answer("Главное меню:", reply_markup=get_main_menu())
    await callback_query.answer()

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
            time_left = timedelta(hours=10) - (datetime.now() - last_play)
            if time_left.total_seconds() > 0:
                # Кулдаун удаляется через 10 секунд
                sent = await message.answer(
                    f"⏳ До следующей игры осталось: {format_timedelta(time_left)}",
                    reply_markup=get_main_menu()
                )
                await asyncio.sleep(10)
                await safe_delete(message.chat.id, sent.message_id)
                return
        except Exception as e:
            logging.error(f"Ошибка проверки кулдауна: {e}")

    result = random.choices(
        ["win", "lose", "draw"],
        weights=[WIN_CHANCE, LOSE_CHANCE, DRAW_CHANCE],
        k=1
    )[0]

    if result == "win":
        wins = player.get("wins", 0) + 1
        player["wins"] = wins
        points = random.randint(1, 15)
        player["points"] += points
        rank, wins_needed = get_next_rank(wins)
        phrase = random.choice(WIN_PHRASES[team])
        outcome = f"{phrase}\nПобеда! +{points} очков 🏆\nНовый ранг: {rank}"
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

    rank, wins_needed = get_next_rank(player["wins"])

    # Результат матча — остаётся навсегда!
    await message.answer(
        f"{outcome}\n\n"
        f"🏅 Текущий ранг: {rank}\n"
        f"⭐ Очки: {player['points']}\n"
        f"📈 До следующего ранга: {wins_needed} побед\n"
        f"🎯 Побед: {player['wins']}",
        reply_markup=get_main_menu()
    )

@dp.message(F.new_chat_members)
async def welcome_new_chat(message: types.Message):
    for new_member in message.new_chat_members:
        if new_member.id == bot.id:
            welcome_text = (
                "🎮 <b>CS:GO Match Bot</b>\n\n"
                "<b>Основные команды:</b>\n"
                "• /t или кнопка 💣 Террористы - играть за террористов\n"
                "• /ct или кнопка 🛡️ Спецназ - играть за спецназ\n"
                "• /stats или кнопка 📊 Моя статистика - ваша статистика\n"
                "• /promo и промокод- ввод промокода\n"
                "• /top или кнопка 🏆 Топ игроков - топ игроков чата\n"
                "• /open или кнопка 🎁 Открыть кейс - открыть кейс со скинами\n\n"
                "<b>Как играть:</b>\n"
                "1. Выберите команду (Террористы/Спецназ)\n"
                "2. Бот определит результат матча\n"
                "3. Получайте очки и повышайте ранг\n"
                "4. Играть можно 1 раз в 10 часов в каждом чате\n\n"
                "<b>Система рангов:</b>\n"
                "• Ранги от Silver 1 до Challenger💎\n"
                "• За победы получаете очки (1-15 за победу)\n"
                "• За поражения теряете очки (1-10 за поражение)\n"
                "• Ничья не изменяет количество очков\n\n"
                "<b>Система кейсов:</b>\n"
                "• Можно открывать кейсы за очки\n"
                "• Чем дороже кейс - тем лучше скины\n"
                "• Редкие скины выпадают редко"
            )
            await message.reply(welcome_text, reply_markup=get_main_menu(), parse_mode="HTML")

# Инициализация при старте
load_promo_uses()

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
