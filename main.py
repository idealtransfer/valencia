import os
import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

# 1. НАСТРОЙКИ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io"

bot = Bot(token=TOKEN)
dp = Dispatcher()
routes = web.RouteTableDef()

# Вспомогательная функция для ответов (защита от CORS ошибок)
def json_response(data, status=200):
    return web.json_response(
        data,
        status=status,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        }
    )

# 2. ОТДАЕМ САЙТ (Главная страница)
@routes.get('/')
async def index_handler(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return web.Response(text=f.read(), content_type='text/html')
    except Exception as e:
        logger.error(f"Error loading index.html: {e}")
        return web.Response(text="Site is loading...", status=500)

# 3. ПРИНИМАЕМ ЗАКАЗ (API)
@routes.post('/api/send')
async def submit_order_handler(request):
    try:
        data = await request.json()
        logger.info(f"New Order Received: {data}")
        
        # Формируем красивое сообщение для Админа
        text = (
            f"🚖 <b>НОВЫЙ ЗАКАЗ</b>\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Имя:</b> {data.get('name')}\n"
            f"📞 <b>Телефон:</b> {data.get('phone')}\n"
            f"📱 <b>Ник в ТГ:</b> {data.get('nick')}\n"
            f"💬 <b>Связь:</b> {data.get('contact_method')}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📍 <b>Откуда:</b> {data.get('pickup')}\n"
            f"🏁 <b>Куда:</b> {data.get('destination')}\n"
            f"📅 <b>Дата:</b> {data.get('date')} ⏰ {data.get('time')}\n"
            f"✈️ <b>Рейс:</b> {data.get('flight', '-')}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"👥 <b>Пассажиры:</b> {data.get('adults')} взр.\n"
            f"🧳 <b>Багаж:</b> {data.get('luggage', 0)}\n"
            f"👶 <b>Дети:</b> Бустер: {data.get('booster', 0)} | Кресло: {data.get('child_seat', 0)}\n"
            f"💳 <b>Оплата:</b> {data.get('payment')}\n"
            f"📝 <b>Пожелания:</b> {data.get('comments', '-')}"
        )

        # Отправка Админу
        if ADMIN_ID:
            try:
                await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
            except Exception as e:
                logger.error(f"Telegram Send Error: {e}")

        # Отправка Клиенту (подтверждение)
        user_id = data.get('user_id')
        if user_id:
            try:
                await bot.send_message(
                    chat_id=user_id, 
                    text="✅ <b>Ваша заявка принята!</b>\nМы свяжемся с вами в ближайшее время для подтверждения.",
                    parse_mode="HTML"
                )
            except Exception:
                pass # Если клиент заблокировал бота, не падаем

        return json_response({'status': 'ok'})

    except Exception as e:
        logger.error(f"API Processing Error: {e}")
        return json_response({'error': str(e)}, status=500)

# Обработка pre-flight запросов браузера (чтобы не было ошибок 405/CORS)
@routes.options('/api/send')
async def options_handler(request):
    return web.Response(status=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type"
    })

# 4. КОМАНДА /START
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "Чтобы заказать трансфер, нажмите синюю кнопку <b>«Меню»</b> или <b>«Заказать трансфер»</b> внизу экрана.",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )

# 5. ЗАПУСК ПРИЛОЖЕНИЯ
async def main():
    app = web.Application()
    app.add_routes(routes)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Amvera требует порт 80
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logger.info("✅ Server started on port 80")
    
    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
