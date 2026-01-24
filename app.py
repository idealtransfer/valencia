import os
import json
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove, WebAppInfo # <-- Вот этот импорт был нужен!

# Настройка логов
logging.basicConfig(level=logging.INFO)

# --- ВАШИ ПЕРЕМЕННЫЕ ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io" 
# -----------------------

bot = Bot(token=TOKEN)
dp = Dispatcher()
routes = web.RouteTableDef()

# 1. ОТДАЕМ САЙТ
@routes.get('/')
async def index_handler(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
    except Exception:
        return web.Response(text="<h1>Сайт работает</h1>", content_type='text/html')

# 2. КОМАНДА /START (Без кнопки, просто текст)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # ReplyKeyboardRemove() удалит старые кнопки, если они остались
    await message.answer(
        "👋 Привет! Я бот для заказа трансфера.\n\n"
        "Чтобы оформить заказ, нажмите на синюю кнопку <b>«Меню»</b> (или «Заказать») слева от поля ввода текста.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove() 
    )

# 3. ЛОВИМ ДАННЫЕ (На случай, если Telegram позволит их прислать)
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        text = (
            f"✅ <b>НОВЫЙ ЗАКАЗ!</b>\n"
            f"👤 <b>Имя:</b> {data.get('name')}\n"
            f"📞 <b>Тел:</b> {data.get('phone')} ({data.get('contact_method')})\n"
            f"🛫 <b>Откуда:</b> {data.get('pickup')}\n"
            f"🏨 <b>Куда:</b> {data.get('destination')}\n"
            f"📅 <b>Дата:</b> {data.get('date')} {data.get('time')}\n"
            f"💰 <b>Оплата:</b> {data.get('payment')}\n"
            f"✈️ <b>Рейс:</b> {data.get('flight')}\n"
            f"🧳 <b>Багаж:</b> {data.get('luggage')}\n"
            f"👶 <b>Дети:</b> Бустер: {data.get('booster')}, Кресло: {data.get('child_seat')}\n"
            f"📝 <b>Коммент:</b> {data.get('comments')}"
        )
        
        # Если данные пришли через sendData - отвечаем
        await message.answer("✅ Заявка принята! Мы скоро свяжемся с вами.")
        if ADMIN_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
            
    except Exception as e:
        logging.error(f"Error handling data: {e}")

# ЗАПУСК
async def main():
    # Сайт
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logging.info("Site started on port 80")

    # Бот
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
