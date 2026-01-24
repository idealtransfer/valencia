import os
import json
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

logging.basicConfig(level=logging.INFO)

# --- ВАШИ ПЕРЕМЕННЫЕ ---
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
# ВСТАВЬТЕ ССЫЛКУ НИЖЕ (Обязательно https://...)
WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io" 
# -----------------------

bot = Bot(token=TOKEN)
dp = Dispatcher()
routes = web.RouteTableDef()

# 1. ОТДАЕМ САЙТ (index.html)
@routes.get('/')
async def index_handler(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
    except Exception:
        return web.Response(text="<h1>Сайт работает!</h1><p>Но файл index.html не найден.</p>", content_type='text/html')

# 2. ПРИСЫЛАЕМ КНОПКУ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚖 Заказать сейчас", web_app=WebAppInfo(url=WEBAPP_URL))]
    ], resize_keyboard=True)
    await message.answer("Для заказа трансфера нажмите кнопку:", reply_markup=kb)

# 3. ЛОВИМ ДАННЫЕ (Самое важное!)
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        text = (
            f"✅ <b>НОВЫЙ ЗАКАЗ!</b>\n"
            f"👤 <b>Кто:</b> {data.get('name')}\n"
            f"📞 <b>Тел:</b> {data.get('phone')} ({data.get('contact_method')})\n"
            f"🚗 <b>Маршрут:</b> {data.get('pickup')} -> {data.get('destination')}\n"
            f"📅 <b>Когда:</b> {data.get('date')} {data.get('time')}"
        )
        
        await message.answer("Супер! Данные получены. Мы свяжемся с вами.")
        if ADMIN_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"Ошибка данных: {e}")

async def main():
    # Запуск сайта на порту 80
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
