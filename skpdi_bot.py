import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определение состояний диалога
DEFECT_ID, REASON = range(2)

# Конфигурация Google Sheets
GOOGLE_SHEETS_CREDENTIALS = 'C:\Users\KhiruntsevVG\Downloads\favorable-array-480015-a4-d9d80ba628c6.json'  # Замените на путь к вашему JSON файлу
SPREADSHEET_NAME = 'НУдаление_дефектов_СКПДИ'  # Замените на название вашей таблицы

# Инициализация Google Sheets
def init_google_sheets():
    try:
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_SHEETS_CREDENTIALS, scope
        )
        client = gspread.authorize(creds)
        worksheet = client.open(SPREADSHEET_NAME).sheet1
        return worksheet
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот для записи дефектов.\n"
        "Для начала введите команду /report"
    )

# Команда /report - начало диалога
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Пожалуйста, укажите ID дефекта:"
    )
    return DEFECT_ID

# Обработка ID дефекта
async def get_defect_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username or update.message.from_user.first_name
    defect_id = update.message.text
    
    # Сохраняем данные в контексте
    context.user_data['defect_id'] = defect_id
    context.user_data['user_id'] = user_id
    context.user_data['user_name'] = user_name
    
    await update.message.reply_text(
        "Теперь укажите причину отклонения:"
    )
    return REASON

# Обработка причины отклонения и запись в Google Sheets
async def get_reason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reason = update.message.text
    
    try:
        # Получаем данные из контекста
        defect_id = context.user_data.get('defect_id')
        user_id = context.user_data.get('user_id')
        user_name = context.user_data.get('user_name')
        
        # Инициализируем Google Sheets
        worksheet = init_google_sheets()
        
        if worksheet:
            # Добавляем запись в таблицу
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [defect_id, reason, user_id, user_name, current_time]
            worksheet.append_row(row)
            
            await update.message.reply_text(
                f"✅ Данные успешно записаны в таблицу!\n"
                f"ID дефекта: {defect_id}\n"
                f"Причина: {reason}\n"
                f"Время записи: {current_time}"
            )
        else:
            await update.message.reply_text(
                "❌ Ошибка подключения к Google Sheets. Проверьте настройки."
            )
        
    except Exception as e:
        logger.error(f"Ошибка при записи в Google Sheets: {e}")
        await update.message.reply_text(
            "❌ Произошла ошибка при записи данных. Попробуйте снова."
        )
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    return ConversationHandler.END

# Команда /cancel для отмены диалога
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Диалог отменен. Для начала нового введите /report"
    )
    # Очищаем данные пользователя
    context.user_data.clear()
    return ConversationHandler.END

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступные команды:\n"
        "/start - начать работу с ботом\n"
        "/report - начать отчет о дефекте\n"
        "/help - показать эту справку"
    )

# Основная функция
def main():
    # Замените 'YOUR_BOT_TOKEN' на токен вашего бота
    TOKEN = '7917625529:AAHZ3pK0EhlTLWYxs13femxOHtwxdx2-CAw'
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler для управления диалогом
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('report', report)],
        states={
            DEFECT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_defect_id)],
            REASON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_reason)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(conv_handler)
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
