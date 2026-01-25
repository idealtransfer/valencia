import os
import json
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

# Настройка логов (чтобы видеть ошибки в консоли Amvera)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ПЕРЕМЕННЫЕ ИЗ AMVERA
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
# ВАША ССЫЛКА (Уже вписал её за вас):
WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io" 

bot = Bot(token=TOKEN)
dp = Dispatcher()
routes = web.RouteTableDef()

# 1. ГЛАВНАЯ СТРАНИЦА (Отдает index.html)
@routes.get('/')
async def index_handler(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
    except Exception as e:
        logger.error(f"Error reading index.html: {e}")
        return web.Response(text="Error: index.html not found", status=404)

# 2. ПРИЕМ ЗАКАЗОВ (Вот этого куска у вас сейчас не хватает или он старый!)
@routes.post('/api/send')
async def submit_order_handler(request):
    try:
        # Читаем данные от формы
        data = await request.json()
        logger.info(f"Order received: {data}")
        
        # Формируем красивое сообщение
        text = (
            f"🚕 <b>НОВЫЙ ЗАКАЗ</b>\n"
            f"━━━━━━━━━━━━\n"
            f"👤 <b>Имя:</b> {data.get('name')}\n"
            f"📞 <b>Тел:</b> {data.get('phone')} ({data.get('contact_method')})\n"
            f"📍 <b>Откуда:</b> {data.get('pickup')}\n"
            f"🏁 <b>Куда:</b> {data.get('destination')}\n"
            f"📅 <b>Дата:</b> {data.get('date')} {data.get('time')}\n"
            f"✈️ <b>Рейс:</b> {data.get('flight', '-')}\n"
            f"💳 <b>Оплата:</b> {data.get('payment')}\n"
            f"━━━━━━━━━━━━\n"
            f"👥 <b>Пассажиры:</b> {data.get('adults')} взр.\n"
            f"🧳 <b>Багаж:</b> {data.get('luggage', 0)}\n"
            f"👶 <b>Дети:</b> Бустер: {data.get('booster', 0)} | Кресло: {data.get('child_seat', 0)}\n"
            f"💬 <b>Пожелания:</b> {data.get('comments', '-')}"
        )

        # Отправляем АДМИНУ
        if ADMIN_ID:
            try:
                # Очищаем ID от возможных пробелов
                clean_id = str(ADMIN_ID).strip()
                await bot.send_message(chat_id=clean_id, text=text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to send to admin: {e}")

        # Отправляем КЛИЕНТУ (если есть его ID)
        user_id = data.get('user_id')
        if user_id:
            try:
                await bot.send_message(chat_id=user_id, text="✅ Ваш заказ принят! Мы скоро свяжемся с вами.")
            except Exception as e:
                logger.error(f"Failed to send to user: {e}")

        return web.json_response({'status': 'ok'})

    except Exception as e:
        logger.error(f"Critical error in submit_order: {e}")
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)

# 3. ЛОГИКА БОТА
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Нажмите кнопку <b>«Меню»</b> слева внизу, чтобы заказать трансфер.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

# 4. ЗАПУСК ВСЕГО
async def main():
    # Настройка сервера
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    # Запуск на порту 80 (Обязательно для Amvera)
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logger.info("Server started on port 80")

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
