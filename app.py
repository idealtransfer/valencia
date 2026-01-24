import os
import json
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io" 

bot = Bot(token=TOKEN)
dp = Dispatcher()
routes = web.RouteTableDef()

# 1. ОТДАЕМ САЙТ
@routes.get('/')
async def index_handler(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
    except Exception as e:
        logger.error(f"Index error: {e}")
        return web.Response(text="File index.html not found", status=404)

# 2. ПРИЕМ ЗАКАЗА
@routes.post('/submit_order')
async def submit_order_handler(request):
    try:
        data = await request.json()
        logger.info(f"Received order: {data}")
        
        text = (
            f"🚕 <b>НОВЫЙ ЗАКАЗ</b>\n"
            f"━━━━━━━━━━━━\n"
            f"👤 <b>Имя:</b> {data.get('name')}\n"
            f"📞 <b>Тел:</b> {data.get('phone')} ({data.get('contact_method')})\n"
            f"📍 <b>Откуда:</b> {data.get('pickup')}\n"
            f"🏁 <b>Куда:</b> {data.get('destination')}\n"
            f"📅 <b>Когда:</b> {data.get('date')} в {data.get('time')}\n"
            f"✈️ <b>Рейс:</b> {data.get('flight', '-')}\n"
            f"💳 <b>Оплата:</b> {data.get('payment')}\n"
            f"━━━━━━━━━━━━\n"
            f"👥 <b>Пассажиры:</b> {data.get('adults', 1)} взр.\n"
            f"🧳 <b>Багаж:</b> {data.get('luggage', 0)} шт.\n"
            f"👶 <b>Детские кресла:</b>\n"
            f"   - Бустеры: {data.get('booster', 0)}\n"
            f"   - Автокресла: {data.get('child_seat', 0)}\n"
            f"💬 <b>Пожелания:</b> {data.get('comments', '-')}"
        )

        # Отправка админу
        if ADMIN_ID:
            try:
                # Убираем возможные пробелы из ID
                clean_admin_id = str(ADMIN_ID).strip()
                await bot.send_message(chat_id=clean_admin_id, text=text, parse_mode="HTML")
            except Exception as bot_err:
                logger.error(f"Failed to send to admin: {bot_err}")

        # Отправка клиенту
        user_id = data.get('user_id')
        if user_id:
            try:
                await bot.send_message(chat_id=user_id, text="✅ Заявка принята! Мы скоро свяжемся с вами.")
            except:
                pass

        return web.json_response({'status': 'ok'})
    except Exception as e:
        logger.error(f"Global handler error: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

# 3. КОМАНДА /START
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я готов принять заказ.\n"
        "Нажмите кнопку <b>«Меню»</b> (синяя слева), чтобы открыть форму.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

# ЗАПУСК
async def main():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
