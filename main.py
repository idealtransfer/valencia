import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo

# Получаем настройки из системы
API_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = os.getenv('ADMIN_ID') 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Словарь для ответов самого бота (после отправки формы)
responses = {
    'ru': "✅ Спасибо! Ваш заказ принят. Мы свяжемся с вами в ближайшее время для уточнения деталей и стоимости.",
    'es': "✅ ¡Gracias! Su pedido ha sido recibido. Nos pondremos en contacto con usted pronto para confirmar los detalles y el precio.",
    'en': "✅ Thank you! Your order has been received. We will contact you shortly to clarify details and cost."
}

@dp.message(CommandStart())
async def start(message: types.Message):
    # Текст кнопки на разных языках
    btn_text = "Заказать трансфер 🚗"
    if message.from_user.language_code == 'es':
        btn_text = "Reservar traslado 🚗"
    elif message.from_user.language_code == 'en':
        btn_text = "Book Transfer 🚗"

    markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(
                text=btn_text, 
                web_app=WebAppInfo(url="https://idealtransfer.github.io/valencia/")) # Ссылка на ваш GitHub
            ]
        ],
        resize_keyboard=True
    )
    await message.answer("¡Hola! Нажмите на кнопку ниже, чтобы оформить заявку на трансфер в Валенсии.", reply_markup=markup)

@dp.message(F.web_app_data)
async def handle_order(message: types.Message):
    # Читаем данные из формы
    try:
        data = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("Ошибка при обработке данных.")
        return

    user = message.from_user
    lang = data.get('language', 'ru')
    tg_profile = f"tg://user?id={user.id}"
    
    # Формируем отчет для администратора
    report = (
        f"🆕 *НОВЫЙ ЗАКАЗ (Язык: {lang})*\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📍 *Откуда:* {data.get('pickup')}\n"
        f"🏁 *Куда:* {data.get('destination')}\n"
        f"📅 *Дата:* {data.get('date')} | ⏰ {data.get('time')}\n"
        f"✈️ *Рейс:* {data.get('flight') or '—'}\n\n"
        f"👥 *Пассажиры:*\n"
        f"• Взрослые: {data.get('adults') or 1}\n"
        f"• Бустеры: {data.get('booster') or 0}\n"
        f"• Кресла: {data.get('child_seat') or 0}\n"
        f"🧳 *Багаж:* {data.get('luggage') or 0} шт.\n\n"
        f"💳 *Оплата:* {data.get('payment', '').upper()}\n"
        f"📝 *Пожелания:* {data.get('comments') or '—'}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 *Имя:* {data.get('name')}\n"
        f"📱 *Тел:* {data.get('phone')}\n"
        f"💬 *Связь через:* {data.get('contact_method')}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔗 [ПРОФИЛЬ ЗАКАЗЧИКА]({tg_profile})"
    )
    
    # Отвечаем пользователю на его языке
    thanks_text = responses.get(lang, responses['ru'])
    await message.answer(thanks_text)
    
    # Отправляем уведомление вам
    await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
