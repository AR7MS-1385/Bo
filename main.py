# main.py

import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiohttp import web   # 👈 اضافه شد برای وب‌سرور ساده

from store import Store   # کلاس Store

# -------------------- تنظیمات --------------------
API_TOKEN = "8242095365:AAFLAkNkNbdtmlCZbmUZtmgNVrmFEUo-KkQ"
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

store = Store()

# -------------------- منو --------------------
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ افزودن محصول"), KeyboardButton(text="💰 فروش محصول")],
        [KeyboardButton(text="🔍 جستجو"), KeyboardButton(text="📦 همه محصولات")],
        [KeyboardButton(text="❌ حذف محصول"), KeyboardButton(text="🗑️ حذف همه محصولات")]
    ],
    resize_keyboard=True
)

# -------------------- حالت‌ها --------------------
class AddProductFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_number = State()

class SellProductFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_number = State()

class SearchProductFSM(StatesGroup):
    waiting_for_name = State()

class DeleteProductFSM(StatesGroup):
    waiting_for_name = State()

# -------------------- دستورات --------------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("سلام 👋\nیکی از گزینه‌ها رو انتخاب کن:", reply_markup=main_kb)

# ------------- افزودن محصول ----------------
@dp.message(F.text == "➕ افزودن محصول")
async def add_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصول را وارد کنید:")
    await state.set_state(AddProductFSM.waiting_for_name)

@dp.message(AddProductFSM.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("قیمت محصول را وارد کنید (به تومان):")
    await state.set_state(AddProductFSM.waiting_for_price)

@dp.message(AddProductFSM.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("⚠️ لطفاً عدد معتبر وارد کن.")
        return
    await state.update_data(price=price)
    await message.answer("تعداد محصول را وارد کنید:")
    await state.set_state(AddProductFSM.waiting_for_number)

@dp.message(AddProductFSM.waiting_for_number)
async def process_number(message: Message, state: FSMContext):
    try:
        number = int(message.text)
    except ValueError:
        await message.answer("⚠️ لطفاً عدد معتبر وارد کن.")
        return

    data = await state.get_data()
    name = data["name"]
    price = data["price"]

    ok = store.add_product(name, price, number)
    if ok:
        await message.answer(f"✅ محصول '{name}' با قیمت {price} و تعداد {number} اضافه شد.", reply_markup=main_kb)
    else:
        await message.answer("❌ محصولی با این نام وجود دارد.", reply_markup=main_kb)

    await state.clear()

# ------------- فروش محصول ----------------
@dp.message(F.text == "💰 فروش محصول")
async def sell_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصولی که می‌خواید بفروشید را وارد کنید:")
    await state.set_state(SellProductFSM.waiting_for_name)

@dp.message(SellProductFSM.waiting_for_name)
async def sell_process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("تعداد محصول را وارد کنید:")
    await state.set_state(SellProductFSM.waiting_for_number)

@dp.message(SellProductFSM.waiting_for_number)
async def sell_process_number(message: Message, state: FSMContext):
    try:
        number = int(message.text)
    except ValueError:
        await message.answer("⚠️ لطفاً عدد معتبر وارد کن.")
        return

    data = await state.get_data()
    name = data["name"]
    result = store.sell_product(name, number)
    await message.answer(result, reply_markup=main_kb)
    await state.clear()

# ------------- جستجوی پیشرفته ----------------
@dp.message(F.text == "🔍 جستجو")
async def search_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصول یا قسمتی از آن را وارد کنید:")
    await state.set_state(SearchProductFSM.waiting_for_name)

@dp.message(SearchProductFSM.waiting_for_name)
async def search_process_name(message: Message, state: FSMContext):
    keyword = message.text
    results = store.search_products_partial(keyword)
    if results:
        msg = "📦 محصولات پیدا شده:\n"
        for p in results:
            msg += f"{p[1]} - {p[2]} تومان - تعداد {p[3]}\n"
        await message.answer(msg, reply_markup=main_kb)
    else:
        await message.answer("❌ محصولی پیدا نشد.", reply_markup=main_kb)
    await state.clear()

# ------------- نمایش همه محصولات ----------------
@dp.message(F.text == "📦 همه محصولات")
async def show_all_products(message: Message):
    store.load_products_from_db()
    if not store.products:
        await message.answer("هیچ محصولی وجود ندارد.", reply_markup=main_kb)
        return
    msg = "📋 همه محصولات:\n"
    for p in store.products:
        msg += f"{p[1]} - {p[2]} تومان - تعداد {p[3]}\n"
    await message.answer(msg, reply_markup=main_kb)

# ------------- حذف محصول ----------------
@dp.message(F.text == "❌ حذف محصول")
async def delete_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصولی که می‌خواید حذف کنید را وارد کنید:")
    await state.set_state(DeleteProductFSM.waiting_for_name)

@dp.message(DeleteProductFSM.waiting_for_name)
async def delete_product_process(message: Message, state: FSMContext):
    name = message.text
    ok = store.delete_product(name)
    if ok:
        await message.answer(f"✅ محصول '{name}' حذف شد.", reply_markup=main_kb)
    else:
        await message.answer("❌ محصول پیدا نشد.", reply_markup=main_kb)
    await state.clear()

# ------------- حذف همه محصولات ----------------
@dp.message(F.text == "🗑️ حذف همه محصولات")
async def delete_all_products(message: Message):
    store.delete_all_products()
    await message.answer("✅ همه محصولات حذف شدند.", reply_markup=main_kb)

# -------------------- وب‌سرور ساده --------------------
async def health(request):
    return web.Response(text="ok")

async def start_web_app():
    port = int(os.getenv("PORT", "8000"))
    app = web.Application()
    app.add_routes([web.get("/health", health)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on 0.0.0.0:{port}")

# -------------------- اجرا --------------------
async def main():
    # راه‌اندازی وب‌سرور (برای Render)
    await start_web_app()

    # شروع polling ربات
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
