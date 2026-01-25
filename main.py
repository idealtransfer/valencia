import os
import logging
import asyncio
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

# 1. НАСТРОЙКИ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 2. УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК (Ловит вообще всё)
async def universal_handler(request):
    path = request.path
    method = request.method
    
    logger.info(f"REQUEST RECEIVED: {method} {path}") # Пишем в лог всё, что приходит

    # --- СЦЕНАРИЙ 1: Открыли сайт (Главная) ---
    if path == '/' and method == 'GET':
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        except Exception as e:
            return web.Response(text=f"Error reading site: {e}", status=500)

    # --- СЦЕНАРИЙ 2: Отправка формы (API) ---
    # Мы принимаем И /submit_order, И /api/send, чтобы наверняка попасть
    if (path == '/api/send' or path == '/submit_order') and method == 'POST':
        try:
            data = await request.json()
            
            # Текст для админа
            text = (
                f"🚕 <b>НОВЫЙ ЗАКАЗ!</b>\n"
                f"👤 {data.get('name')} {data.get('phone')}\n"
                f"📍 {data.get('pickup')} -> {data.get('destination')}\n"
                f"💰 {data.get('payment')}"
            )
            
            # Отправка в Telegram
            if ADMIN_ID:
                try:
                    await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"Telegram Error: {e}")

            return web.json_response({'status': 'ok'})
        except Exception as e:
            logger.error(f"API Error: {e}")
            return web.json_response({'error': str(e)}, status=500)

    # --- СЦЕНАРИЙ 3: Не найдено ---
    return web.Response(text=f"Page not found. You requested: {path} with method {method}", status=404)

# 3. БОТ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Сервер работает. Откройте меню.", reply_markup=ReplyKeyboardRemove())

# 4. ЗАПУСК
async def main():
    app = web.Application()
    
    # ВАЖНО: Мы говорим серверу ловить ЛЮБОЙ запрос (*) одной функцией
    app.router.add_route('*', '/{tail:.*}', universal_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logger.info("NUCLEAR SERVER STARTED ON PORT 80")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
