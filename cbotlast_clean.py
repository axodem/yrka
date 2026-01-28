import asyncio
from datetime import datetime, timedelta, time, timezone

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
import os

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = "godfather_yaris"
ADMIN_ID = 7243901114

# MSK = UTC+3 (TERMUX SAFE)
MSK_TZ = timezone(timedelta(hours=3))
WORK_START = time(9, 0)
WORK_END = time(23, 0)

bot = Bot(
    BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

# ================= FSM =================
class SellUSDT(StatesGroup):
    phone = State()
    name = State()
    card = State()
    bank = State()
    amount = State()
    ready_to_send = State()

# ================= KEYBOARDS =================
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="💰 Продать USDT"),
        KeyboardButton(text="💱 Курс"),
    )
    builder.add(
        KeyboardButton(text="🏛️ Сотрудничество"),
        KeyboardButton(text="🕘 График работы"),
    )
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="‹ Назад")]],
        resize_keyboard=True
    )

def menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Меню")]],
        resize_keyboard=True
    )

def sell_menu_kb(all_filled=False):
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="📱 Телефон"),
        KeyboardButton(text="👤 ФИО"),
        KeyboardButton(text="💳 Карта"),
        KeyboardButton(text="🏦 Банк"),
        KeyboardButton(text="💵 Количество USDT"),
    )
    if all_filled:
        builder.add(KeyboardButton(text="📄 Отправить чек USDT"))
    builder.add(KeyboardButton(text="❌ Меню"))
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# ================= TIME =================
def now_msk():
    return datetime.now(timezone.utc).astimezone(MSK_TZ)

def is_work_time():
    t = now_msk().time()
    return WORK_START <= t < WORK_END

def time_until_work():
    now = now_msk()
    start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    if now.time() < WORK_START:
        delta = start - now
    else:
        delta = start + timedelta(days=1) - now
    h, rem = divmod(int(delta.total_seconds()), 3600)
    m = rem // 60
    return f"{h} ч {m} мин"

# ================= START / MENU =================
@dp.message(Command("start"))
@dp.message(F.text == "❌ Меню")
async def start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        (
            "🏠 <b>YarisChange</b>\n"
            "<i>Надёжный обмен USDT</i>\n\n"
            "💸 <b>Лимит:</b> до <b>500$</b>\n"
            f"🆘 <b>Поддержка:</b> @{ADMIN_USERNAME}"
        ),
        reply_markup=main_menu()
    )

# ================= КУРС =================
@dp.message(F.text == "💱 Курс")
async def rate(msg: Message):
    await msg.answer(
        (
            "📊 <b>Динамический курс USDT</b>\n\n"
            "• <b>до 23$</b> — 82.16 RUB/$\n"
            "• <b>23–34$</b> — 83.4 RUB/$\n"
            "• <b>34–150$</b> — 85.11 RUB/$\n"
            "• <b>150–300$</b> — 85.9 RUB/$\n"
            "• <b>300$+</b> — 87.16 RUB/$\n\n"
            "<b>Минимум: 10 USDT</b>"
        ),
        reply_markup=menu_kb()
    )

# ================= СОТРУДНИЧЕСТВО =================
@dp.message(F.text == "🏛️ Сотрудничество")
async def cooperation(msg: Message):
    await msg.answer(
        (
            "⚓ <b>Сотрудничество и привилегии</b>\n\n"
            "> <i><b>Повышенный курс</b></i>\n"
            "> <i><b>Процент со сделок</b></i>\n\n"
            "🥇 <b>Интересует?</b>\n"
            f"<b>Писать @{ADMIN_USERNAME}</b>"
        ),
        reply_markup=menu_kb()
    )

# ================= ГРАФИК =================
@dp.message(F.text == "🕘 График работы")
async def schedule(msg: Message):
    await msg.answer(
        (
            "📄 <b>График работы</b>\n\n"
            "<b>Ежедневно с 09:00 до 23:00</b>\n"
            "<b>По московскому времени (МСК)</b>\n\n"
            f"🥇 <b>Любые вопросы — @{ADMIN_USERNAME}</b>"
        ),
        reply_markup=menu_kb()
    )

# ================= ПРОДАЖА =================
@dp.message(F.text == "💰 Продать USDT")
async def sell(msg: Message, state: FSMContext):
    if not is_work_time():
        await msg.answer(
            (
                "❌ <b>Мы сейчас не работаем</b>\n\n"
                f"⏳ <b>До начала работы осталось:</b> {time_until_work()}\n"
                "<b>Ориентир — МСК</b>"
            ),
            reply_markup=main_menu()
        )
        return

    data = await state.get_data()
    fields = {
        "phone": "📱 Телефон",
        "name": "👤 ФИО",
        "card": "💳 Карта",
        "bank": "🏦 Банк",
        "amount": "💵 Количество USDT"
    }

    text = "<b>YarisChange — оформление заявки</b>\n\n"
    all_filled = True

    for key, label in fields.items():
        value = data.get(key)
        if value:
            text += f"{label}: <b>{value}</b>\n"
        else:
            text += f"{label}: <i>не указано</i>\n"
            if key in ["phone", "name", "bank", "amount"]:
                all_filled = False

    await msg.answer(text, reply_markup=sell_menu_kb(all_filled))

# ================= SET FIELDS =================
field_map = {
    "📱 Телефон": ("phone", "📱 <b>Введите номер телефона</b>\n\n> <b>79998887766</b>"),
    "👤 ФИО": ("name", "👤 <b>Введите ФИО получателя</b>\n\n> <b>Иванов Иван Иванович</b>"),
    "💳 Карта": ("card", "💳 <b>Введите карту</b>\n\n> <i>Необязательно</i>"),
    "🏦 Банк": ("bank", "🏦 <b>Введите банк</b>\n\n> <b>Сбербанк</b>"),
    "💵 Количество USDT": ("amount", "💵 <b>Введите количество USDT</b>\n\n> <b>Минимум 10</b>")
}

@dp.message(F.text.in_(list(field_map.keys())))
async def set_field(msg: Message, state: FSMContext):
    field, prompt = field_map[msg.text]
    await state.set_state(getattr(SellUSDT, field))
    await msg.answer(prompt, reply_markup=back_kb())

@dp.message(F.text == "‹ Назад")
async def back(msg: Message, state: FSMContext):
    await sell(msg, state)

# ================= USER INPUT =================
async def update_field_and_check(msg: Message, state: FSMContext, field_name: str):
    await state.update_data(**{field_name: msg.text})
    data = await state.get_data()
    required = ["phone", "name", "bank", "amount"]

    if all(data.get(f) for f in required):
        await state.set_state(SellUSDT.ready_to_send)
        await msg.answer(
            (
                "✅ <b>Все обязательные поля заполнены</b>\n\n"
                "📄 <b>Создайте чек через CryptoBot</b>\n"
                f"📨 <b>Отправьте чек @{ADMIN_USERNAME}</b>"
            ),
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="✅ Сделано")],
                    [KeyboardButton(text="❌ Меню")]
                ],
                resize_keyboard=True
            )
        )
    else:
        await sell(msg, state)

@dp.message(SellUSDT.phone)
async def phone(msg: Message, state: FSMContext):
    await update_field_and_check(msg, state, "phone")

@dp.message(SellUSDT.name)
async def name(msg: Message, state: FSMContext):
    await update_field_and_check(msg, state, "name")

@dp.message(SellUSDT.card)
async def card(msg: Message, state: FSMContext):
    await update_field_and_check(msg, state, "card")

@dp.message(SellUSDT.bank)
async def bank(msg: Message, state: FSMContext):
    await update_field_and_check(msg, state, "bank")

@dp.message(SellUSDT.amount)
async def amount(msg: Message, state: FSMContext):
    await update_field_and_check(msg, state, "amount")

# ================= DONE =================
@dp.message(F.text == "✅ Сделано")
async def done(msg: Message, state: FSMContext):
    data = await state.get_data()
    required = ["phone", "name", "bank", "amount"]

    if not all(data.get(f) for f in required):
        await msg.answer("❌ <b>Заполните все обязательные поля</b>")
        return

    admin_text = (
        "💰 <b>НОВАЯ ПРОДАЖА USDT</b>\n\n"
        f"👤 Клиент: @{msg.from_user.username or 'Нет username'}\n"
        f"📱 Телефон: {data.get('phone')}\n"
        f"👤 ФИО: {data.get('name')}\n"
        f"💳 Карта: {data.get('card','не указана')}\n"
        f"🏦 Банк: {data.get('bank')}\n"
        f"💵 USDT: {data.get('amount')}"
    )

    await bot.send_message(ADMIN_ID, admin_text)
    await msg.answer(
        "💸 <b>Заявка отправлена</b>\n<i>Ожидайте проверки</i>",
        reply_markup=main_menu()
    )
    await state.clear()

# ================= RUN =================
async def main():
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())
