import os
import logging
import asyncio
import json
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardRemove

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')
WEBAPP_URL = "idealtransfer-idealtransfer.amvera.io"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ФУНКЦИЯ ДЛЯ КОРРЕКТНОГО ОТВЕТА (CORS) ---
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

async def universal_handler(request):
    path = request.path
    method = request.method
    
    logger.info(f"⚡ ЗАПРОС ПРИШЕЛ: {method} {path}")

    # 1. ОБРАБОТКА OPTIONS (Браузер спрашивает разрешения)
    if method == 'OPTIONS':
        return web.Response(status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        })

    # 2. ОТДАЕМ САЙТ (GET /)
    if path == '/' and method == 'GET':
        try:
            with open('index.html', 'r', encoding='utf-8') as f:
                return web.Response(text=f.read(), content_type='text/html')
        except Exception as e:
            return web.Response(text=f"Error: {e}", status=500)

    # 3. ПРИНИМАЕМ ЗАКАЗ (POST /api/send)
    if path == '/api/send' and method == 'POST':
        try:
            data = await request.json()
            
            # Текст для админа
            text = (
                f"🚕 <b>НОВЫЙ ЗАКАЗ</b>\n"
                f"👤 {data.get('name')} | {data.get('phone')}\n"
                f"📍 {data.get('pickup')} -> {data.get('destination')}\n"
                f"💰 {data.get('payment')} | ✈️ {data.get('flight', '-')}"
            )
            
            # Отправка в Telegram
            if ADMIN_ID:
                try:
                    await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"TG Error: {e}")

            return json_response({'status': 'ok'})
        except Exception as e:
            logger.error(f"API Error: {e}")
            return json_response({'error': str(e)}, status=500)

    return web.Response(text="Not Found", status=404)

# БОТ
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Сервер работает. Жмите кнопку меню.", reply_markup=ReplyKeyboardRemove())

async def main():
    app = web.Application()
    # Ловим ВООБЩЕ ВСЁ (*)
    app.router.add_route('*', '/{tail:.*}', universal_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logger.info("✅ SERVER STARTED WITH CORS SUPPORT")
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
