import os
import json
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiohttp import web

# Настройка логов
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

# --- ВСТАВЬТЕ ВАШУ НОВУЮ ССЫЛКУ НИЖЕ (вместо https://...) ---
WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io"
# -----------------------------------------------------------

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 1. Функция, которая показывает ваш сайт (index.html)
async def index_handler(request):
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except Exception as e:
        return web.Response(text=f"Error loading site: {e}", status=500)

# 2. Команда /start - выдает кнопку с Вашей ссылкой
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚖 Заказать трансфер", web_app=WebAppInfo(url=WEBAPP_URL))]
    ], resize_keyboard=True)

    await message.answer(
        "Привет! Я бот для заказа трансфера.\nНажмите кнопку ниже:",
        reply_markup=kb
    )

# 3. Ловим данные из формы
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        
        # Формируем красивый текст для админа
        order_text = (
            f"🚖 <b>НОВЫЙ ЗАКАЗ</b>\n"
            f"👤 <b>Имя:</b> {data.get('name')}\n"
            f"📞 <b>Тел:</b> {data.get('phone')}\n"
            f"🛫 <b>Откуда:</b> {data.get('pickup')}\n"
            f"🏨 <b>Куда:</b> {data.get('destination')}\n"
            f"📅 <b>Дата:</b> {data.get('date')} {data.get('time')}\n"
            f"💬 <b>Связь:</b> {data.get('contact_method')}"
        )

        # Ответ клиенту
        await message.answer("✅ Спасибо! Заявка принята, скоро напишем.")
        
        # Ответ админу
        if ADMIN_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=order_text, parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"Ошибка данных: {e}")

# 4. Главный запуск (Сайт на порту 80 + Бот)
async def main():
    # Настраиваем веб-сервер
    app = web.Application()
    app.router.add_get('/', index_handler)
    
    # Запускаем его на порту 80
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    await site.start()
    logging.info("Site started on port 80")

    # Удаляем вебхук на всякий случай и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
