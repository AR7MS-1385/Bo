import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiohttp import web
from store import Store

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
        [KeyboardButton(text="✏️ ویرایش محصول"), KeyboardButton(text="📊 گزارش فروش")],
        [KeyboardButton(text="⚠️ موجودی کم"), KeyboardButton(text="🗑️ حذف محصولات")],
        [KeyboardButton(text="📖 نحوه کار با ربات"), KeyboardButton(text="ℹ️ درباره ربات")]
    ],
    resize_keyboard=True
)

# کیبورد کوچک مخصوص حالت‌ها (فقط دکمه منو)
cancel_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 منو")]
    ],
    resize_keyboard=True
)

# کیبورد منوی حذف
delete_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ حذف محصول انتخابی")],
        [KeyboardButton(text="🗑️ حذف همه محصولات")],
        [KeyboardButton(text="🏠 منو")]
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

class EditProductFSM(StatesGroup):
    waiting_for_name = State()
    waiting_for_field = State()
    waiting_for_value = State()

class ReportFSM(StatesGroup):
    waiting_for_start = State()
    waiting_for_end = State()

# -------------------- متن راهنما و درباره --------------------
HELP_TEXT = """
📖 *راهنمای کامل کار با ربات مدیریت فروشگاه*

این ربات برای مدیریت سریع و ساده‌ی محصولات و ثبت فروش طراحی شده است. در ادامه هر قسمت با جزئیات توضیح داده شده:

➕ *افزودن محصول*  
1. دکمه «➕ افزودن محصول» را بزنید.  
2. *نام محصول* را وارد کنید (مثال: `موبایل A`).  
3. *قیمت* را به تومان وارد کنید (عدد صحیح، مثال: `3500000`).  
4. *تعداد* را وارد کنید (عدد صحیح، مثال: `10`).  
✅ بعد از اتمام، محصول به لیست اضافه می‌شود و منوی اصلی نمایش داده می‌شود.

💰 *فروش محصول*  
1. دکمه «💰 فروش محصول» را بزنید.  
2. نام محصول را وارد کنید.  
3. تعداد فروخته‌شده را وارد کنید.  
- اگر موجودی کافی نباشد پیام هشدار دریافت می‌کنید.  
- فروش ثبت می‌شود و موجودی کاهش می‌یابد.

🔍 *جستجو*  
- دکمه «🔍 جستجو» را بزنید و نام کامل یا بخشی از نام محصول را تایپ کنید تا محصولات مشابه نمایش داده شوند.

📦 *همه محصولات*  
- دکمه «📦 همه محصولات» لیست کامل محصولات را همراه با قیمت و تعداد موجود نمایش می‌دهد.

✏️ *ویرایش محصول*  
1. دکمه «✏️ ویرایش محصول» را بزنید.  
2. نام محصولی که می‌خواهید ویرایش کنید را وارد کنید.  
3. انتخاب کنید کدام فیلد را تغییر دهید: `نام` / `قیمت` / `تعداد`.  
4. مقدار جدید را وارد کنید.  
✅ تغییر ذخیره می‌شود.

📊 *گزارش فروش*  
1. دکمه «📊 گزارش فروش» را بزنید.  
2. تاریخ شروع را وارد کنید (مثال تقویم جلالی: `01-07-1403`).  
3. تاریخ پایان را وارد کنید (مثال: `10-07-1403`).  
- ربات فروش‌های ثبت‌شده در آن بازه و مجموع مبلغ را نمایش می‌دهد.

⚠️ *موجودی کم*  
- این بخش محصولاتی را نشان می‌دهد که موجودی آن‌ها **۰ یا ۱** است.  
- از این بخش برای یادآوری سفارش مجدد استفاده کنید.

🗑️ *حذف محصولات*  
- با زدن «🗑️ حذف محصولات» منوی حذف نمایش داده می‌شود:  
  - ❌ حذف محصول انتخابی — نام محصول را وارد کن تا آن محصول حذف شود.  
  - 🗑️ حذف همه محصولات — تمام محصولات پاک می‌شوند (با احتیاط استفاده شود).

🏠 *منو*  
- در هر مرحله اگر خواستی کار را متوقف کنی یا به منوی اصلی برگردی، دکمه «🏠 منو» را بزن.

---

🔔 *نکات مهم*:  
- برای فیلدهای عددی فقط عدد صحیح وارد کنید.  
- برای تاریخ‌ها از قالب `dd-mm-yyyy` (جلالی) استفاده کن.  
- حذف همه محصولات غیرقابل بازگشت است — قبل از زدن آن مطمئن شو.
"""

ABOUT_TEXT = """
ℹ️ *درباره ربات مدیریت فروشگاه*

این ربات برای مدیریت ساده و سریع موجودی و فروش محصولات طراحی شده است.  
با این ربات می‌توانید:
- محصولات را ثبت و ویرایش کنید،  
- فروش‌ها را ثبت کنید و گزارش بگیرید،  
- محصولات با موجودی کم را مرور کنید،  
- و در صورت نیاز محصولات را حذف کنید.

📌 *قابلیت‌های کلیدی*: ثبت محصول، ثبت فروش، گزارش‌گیری بر پایه تاریخ، هشدار موجودی کم (۰ یا ۱)، حذف تکی یا کلی محصولات.

👨‍💻 *توسعه‌دهنده*: (امیررضا محمدی سخا )  
📅 نسخه: 1.0
"""

# -------------------- دکمه منو (همیشه فعال) --------------------
@dp.message(F.text == "🏠 منو")
async def go_to_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🏠 منوی اصلی:", reply_markup=main_kb)

# -------------------- دستورات --------------------
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("سلام 👋\nیکی از گزینه‌ها رو انتخاب کن:", reply_markup=main_kb)

# -------------------- نمایش راهنما و درباره --------------------
@dp.message(F.text == "📖 نحوه کار با ربات")
async def how_to_use(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HELP_TEXT, parse_mode="Markdown", reply_markup=main_kb)

@dp.message(F.text == "ℹ️ درباره ربات")
async def about_bot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(ABOUT_TEXT, parse_mode="Markdown", reply_markup=main_kb)

# ------------- افزودن محصول ----------------
@dp.message(F.text == "➕ افزودن محصول")
async def add_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصول را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(AddProductFSM.waiting_for_name)

@dp.message(AddProductFSM.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("قیمت محصول را وارد کنید (به تومان):", reply_markup=cancel_kb)
    await state.set_state(AddProductFSM.waiting_for_price)

@dp.message(AddProductFSM.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ فقط عدد صحیح وارد کن.", reply_markup=cancel_kb)
        return
    await state.update_data(price=int(message.text))
    await message.answer("تعداد محصول را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(AddProductFSM.waiting_for_number)

@dp.message(AddProductFSM.waiting_for_number)
async def process_number(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ فقط عدد صحیح وارد کن.", reply_markup=cancel_kb)
        return
    data = await state.get_data()
    name = data["name"]
    price = data["price"]
    number = int(message.text)

    ok = store.add_product(name, price, number)
    if ok:
        await message.answer(f"✅ محصول '{name}' با قیمت {price} و تعداد {number} اضافه شد.", reply_markup=main_kb)
    else:
        await message.answer("❌ محصولی با این نام وجود دارد.", reply_markup=main_kb)
    await state.clear()

# ------------- فروش محصول ----------------
@dp.message(F.text == "💰 فروش محصول")
async def sell_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصولی که می‌خواید بفروشید را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(SellProductFSM.waiting_for_name)

@dp.message(SellProductFSM.waiting_for_name)
async def sell_process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("تعداد محصول را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(SellProductFSM.waiting_for_number)

@dp.message(SellProductFSM.waiting_for_number)
async def sell_process_number(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ عدد صحیح وارد کن.", reply_markup=cancel_kb)
        return
    data = await state.get_data()
    name = data["name"]
    number = int(message.text)
    result = store.sell_product(name, number)
    await message.answer(result, reply_markup=main_kb)
    await state.clear()

# ------------- جستجو ----------------
@dp.message(F.text == "🔍 جستجو")
async def search_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصول یا قسمتی از آن را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(SearchProductFSM.waiting_for_name)

@dp.message(SearchProductFSM.waiting_for_name)
async def search_process_name(message: Message, state: FSMContext):
    keyword = message.text
    results = store.search_products_partial(keyword)
    if results:
        msg = "📦 محصولات پیدا شده:\n"
        for p in results:
            msg += f"\u202B{p[1]} - {int(p[2])} تومان - تعداد {p[3]}\u202C\n"
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
        msg += f"\u202B{p[1]} - {int(p[2])} تومان - تعداد {p[3]}\u202C\n"
    await message.answer(msg, reply_markup=main_kb)

# ------------- موجودی کم ----------------
@dp.message(F.text == "⚠️ موجودی کم")
async def show_low_stock(message: Message):
    results = store.get_low_stock()
    if not results:
        await message.answer("✅ همه محصولات موجودی کافی دارند.", reply_markup=main_kb)
        return
    msg = "⚠️ محصولات با موجودی کم (۰ یا ۱):\n"
    for p in results:
        msg += f"\u202B{p[1]} - {int(p[2])} تومان - تعداد {p[3]}\u202C\n"
    await message.answer(msg, reply_markup=main_kb)

# ------------- ویرایش محصول ----------------
@dp.message(F.text == "✏️ ویرایش محصول")
async def edit_product_start(message: Message, state: FSMContext):
    await message.answer("نام محصولی که می‌خواهید ویرایش کنید را وارد کنید:", reply_markup=cancel_kb)
    await state.set_state(EditProductFSM.waiting_for_name)

@dp.message(EditProductFSM.waiting_for_name)
async def edit_choose_field(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("چه چیزی رو میخوای تغییر بدی؟ (نام / قیمت / تعداد)", reply_markup=cancel_kb)
    await state.set_state(EditProductFSM.waiting_for_field)

@dp.message(EditProductFSM.waiting_for_field)
async def edit_field(message: Message, state: FSMContext):
    field = message.text.strip()
    mapping = {"نام": "name", "قیمت": "price", "تعداد": "number"}
    if field not in mapping:
        await message.answer("⚠️ فقط یکی از اینا: نام / قیمت / تعداد", reply_markup=cancel_kb)
        return
    await state.update_data(field=mapping[field])
    await message.answer("مقدار جدید رو وارد کن:", reply_markup=cancel_kb)
    await state.set_state(EditProductFSM.waiting_for_value)

@dp.message(EditProductFSM.waiting_for_value)
async def edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    ok = store.edit_product(data["name"], data["field"], message.text)
    if ok:
        await message.answer("✅ محصول ویرایش شد.", reply_markup=main_kb)
    else:
        await message.answer("❌ محصول یافت نشد.", reply_markup=main_kb)
    await state.clear()

# ------------- گزارش فروش ----------------
@dp.message(F.text == "📊 گزارش فروش")
async def report_start(message: Message, state: FSMContext):
    await message.answer("📅 تاریخ شروع را وارد کن (مثال: 01-07-1403):", reply_markup=cancel_kb)
    await state.set_state(ReportFSM.waiting_for_start)

@dp.message(ReportFSM.waiting_for_start)
async def report_get_start(message: Message, state: FSMContext):
    await state.update_data(start=message.text)
    await message.answer("📅 تاریخ پایان را وارد کن (مثال: 10-07-1403):", reply_markup=cancel_kb)
    await state.set_state(ReportFSM.waiting_for_end)

@dp.message(ReportFSM.waiting_for_end)
async def report_get_end(message: Message, state: FSMContext):
    data = await state.get_data()
    sales = store.get_sales_report(data["start"], message.text)
    if not sales:
        await message.answer("❌ هیچ فروشی در این بازه ثبت نشده.", reply_markup=main_kb)
    else:
        msg = "📊 گزارش فروش:\n"
        total = 0
        for s in sales:
            msg += f"\u202B{s[1]} - تعداد {s[2]} - مبلغ {int(s[3])} تومان - تاریخ {s[4]}\u202C\n"
            total += int(s[3])
        msg += f"\n💰 مجموع فروش: {total} تومان"
        await message.answer(msg, reply_markup=main_kb)
    await state.clear()

# ------------- حذف محصولات ----------------
@dp.message(F.text == "🗑️ حذف محصولات")
async def delete_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("یکی از گزینه‌های حذف رو انتخاب کن:", reply_markup=delete_menu_kb)

@dp.message(F.text == "❌ حذف محصول انتخابی")
async def delete_one(message: Message, state: FSMContext):
    await message.answer("نام محصولی که می‌خواهی حذف کنی رو وارد کن:", reply_markup=cancel_kb)
    await state.set_state(DeleteProductFSM.waiting_for_name)

@dp.message(DeleteProductFSM.waiting_for_name)
async def delete_one_process(message: Message, state: FSMContext):
    ok = store.delete_product(message.text)
    if ok:
        await message.answer(f"✅ محصول '{message.text}' حذف شد.", reply_markup=main_kb)
    else:
        await message.answer("❌ محصولی با این نام پیدا نشد.", reply_markup=main_kb)
    await state.clear()

@dp.message(F.text == "🗑️ حذف همه محصولات")
async def delete_all(message: Message, state: FSMContext):
    store.delete_all_products()
    await state.clear()
    await message.answer("🗑️ همه محصولات حذف شدند.", reply_markup=main_kb)

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
    print(f"✅ Web server started on port {port}")

# -------------------- اجرا --------------------
async def main():
    # راه‌اندازی وب‌سرور (برای Render یا Heroku)
    await start_web_app()

    # شروع polling ربات
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
