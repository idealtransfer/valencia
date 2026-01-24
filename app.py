import os
import json
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# Настройка логов, чтобы видеть ошибки в Amvera
logging.basicConfig(level=logging.INFO)

# Получаем переменные
TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID')

# Создаем бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 1. Обработчик команды /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # ВАЖНО: Замените ссылку ниже на ВАШУ ссылку приложения из Amvera!
    # Вы найдете её на главной странице проекта в Amvera (вида https://xxx.amvera.io)
    # Обязательно добавьте /index.html в конце, если нужно, или просто домен.
    # Пока что я ставлю заглушку, ВАМ НУЖНО ЕЁ ПОМЕНЯТЬ.
    WEBAPP_URL = "https://idealtransfer-idealtransfer.amvera.io" 

    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🚖 Заказать трансфер", web_app=WebAppInfo(url=WEBAPP_URL))]
    ], resize_keyboard=True)

    await message.answer(
        "Привет! Я бот для заказа трансфера в Валенсии.\n"
        "Нажми на кнопку ниже, чтобы открыть форму заказа 👇",
        reply_markup=kb
    )

# --- 2. Самая главная часть: Ловим данные из WebApp ---
@dp.message(F.web_app_data)
async def web_app_data_handler(message: types.Message):
    # Получаем данные в виде строки JSON
    data_str = message.web_app_data.data
    
    try:
        # Превращаем строку обратно в словарь
        data = json.loads(data_str)
        
        # Формируем красивый текст заказа
        text = (
            f"🚖 <b>НОВЫЙ ЗАКАЗ!</b>\n\n"
            f"👤 <b>Имя:</b> {data.get('name')}\n"
            f"📞 <b>Телефон:</b> {data.get('phone')}\n"
            f"🛫 <b>Откуда:</b> {data.get('pickup')}\n"
            f"🏨 <b>Куда:</b> {data.get('destination')}\n"
            f"📅 <b>Дата:</b> {data.get('date')} в {data.get('time')}\n"
            f"💬 <b>Связь через:</b> {data.get('contact_method')}\n"
        )
        
        # 1. Отправляем подтверждение пользователю (в чат)
        await message.answer(f"✅ Спасибо, {data.get('name')}! Ваш заказ принят.\nМы свяжемся с вами в ближайшее время.")

        # 2. Отправляем уведомление АДМИНУ (Вам)
        if ADMIN_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
            
    except Exception as e:
        await message.answer(f"Ошибка чтения данных: {e}")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
