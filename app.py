import os
import json
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# --- НАСТРОЙКИ ---
logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

# ВСТАВЬТЕ СЮДА ВАШУ ССЫЛКУ ИЗ AMVERA (Например: https://my-bot.amvera.io)
# Обязательно с https:// и без кавычек внутри кавычек
WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io" 

# --- Инициализация ---
bot = Bot(token=TOKEN)
dp = Dispatcher()
routes = web.RouteTableDef()

# --- 1. САЙТ (Отдает index.html) ---
@routes.get('/')
async def index_handler(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"Сайт сломался: {e}", status=500)

# --- 2. БОТ (Команда /start) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем кнопку, которая открывает сайт внутри Telegram
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚖 Заказать трансфер", web_app=WebAppInfo(url=WEBAPP_URL))]
    ], resize_keyboard=True)

    await message.answer(
        "Привет! Нажмите кнопку ниже, чтобы открыть форму заказа:",
        reply_markup=kb
    )

# --- 3. БОТ (Получение данных из формы) ---
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    try:
        # Декодируем данные, пришедшие от сайта
        data = json.loads(message.web_app_data.data)
        
        # Собираем красивое сообщение
        text = (
            f"🚖 <b>НОВЫЙ ЗАКАЗ</b>\n"
            f"👤 <b>Имя:</b> {data.get('name', '-')}\n"
            f"📞 <b>Связь:</b> {data.get('phone', '-')} ({data.get('contact_method', '-')})\n"
            f"🛫 <b>Откуда:</b> {data.get('pickup', '-')}\n"
            f"🏨 <b>Куда:</b> {data.get('destination', '-')}\n"
            f"📅 <b>Когда:</b> {data.get('date', '-')} в {data.get('time', '-')}\n"
            f"💰 <b>Оплата:</b> {data.get('payment', '-')}\n"
            f"📝 <b>Комментарий:</b> {data.get('comments', '-')}"
        )

        await message.answer("✅ Заявка принята! Мы скоро свяжемся с вами.")
        
        # Пересылаем админу
        if ADMIN_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"Ошибка обработки данных: {e}")

# --- ЗАПУСК ВСЕГО ВМЕСТЕ ---
async def main():
    # 1. Настраиваем веб-сервер для сайта
    app = web.Application()
    app.add_routes(routes)
    
    # Запускаем его (runner)
    runner = web.AppRunner(app)
    await runner.setup()
    # Слушаем порт 80 (для Amvera)
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logging.info("Site started on port 80")

    # 2. Запускаем бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
