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

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
# ВСТАВЬТЕ ВАШУ ССЫЛКУ СЮДА:
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
    except Exception:
        return web.Response(text="Error loading site", status=500)

# 2. НОВЫЙ МЕХАНИЗМ: Принимаем заказ напрямую от сайта
@routes.post('/submit_order')
async def submit_order_handler(request):
    try:
        data = await request.json()
        
        # Формируем текст
        text = (
            f"✅ <b>НОВЫЙ ЗАКАЗ</b> (Site)\n"
            f"👤 <b>Имя:</b> {data.get('name')}\n"
            f"📞 <b>Тел:</b> {data.get('phone')} ({data.get('contact_method')})\n"
            f"🛫 <b>Откуда:</b> {data.get('pickup')}\n"
            f"🏨 <b>Куда:</b> {data.get('destination')}\n"
            f"📅 <b>Дата:</b> {data.get('date')} {data.get('time')}\n"
            f"✈️ <b>Рейс:</b> {data.get('flight')}\n"
            f"💰 <b>Оплата:</b> {data.get('payment')}\n"
            f"🧳 <b>Багаж:</b> {data.get('luggage')}\n"
            f"👶 <b>Дети:</b> Бустер: {data.get('booster')}, Кресло: {data.get('child_seat')}\n"
            f"📝 <b>Коммент:</b> {data.get('comments')}"
        )

        # 1. Отправляем АДМИНУ
        if ADMIN_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")

        # 2. Отправляем КЛИЕНТУ (если есть его ID)
        user_id = data.get('user_id')
        if user_id:
            await bot.send_message(chat_id=user_id, text="✅ Ваш заказ принят! Мы скоро свяжемся с вами.")

        return web.json_response({'status': 'ok'})
    except Exception as e:
        logging.error(f"Order error: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

# 3. КОМАНДА /START (Просто приветствие, удаляем старые кнопки)
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
    logging.info("Server started on port 80")

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
