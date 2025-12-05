import logging
from typing import Dict
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    CallbackContext,
    filters
)
from datetime import datetime
import os
import sys

# Загрузка переменных окружения
from dotenv import load_dotenv
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Определение состояний диалога
DEFECT_ID, REASON = range(2)

# Настройки из переменных окружения
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_CREDS_FILE = os.getenv('GOOGLE_CREDS_FILE', 'credentials.json')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = os.getenv('SHEET_NAME', 'Заявки')

# Настройка Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Проверка наличия обязательных переменных
if not TOKEN:
    logger.error("❌ Токен бота не установлен! Укажите TELEGRAM_BOT_TOKEN в .env файле.")
    sys.exit(1)

if not SPREADSHEET_ID:
    logger.error("❌ SPREADSHEET_ID не установлен! Укажите в .env файле.")
    sys.exit(1)

# Глобальная переменная для кэширования соединения с Google Sheets
_google_sheets_client = None

def get_credentials_path():
    """Получаем путь к файлу credentials"""
    possible_paths = [
        os.path.join(os.path.dirname(__file__), GOOGLE_CREDS_FILE),
        GOOGLE_CREDS_FILE,
        "/opt/skpdi_bot/credentials.json"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Найден файл credentials: {path}")
            return path
    
    logger.error(f"Файл credentials не найден по путям: {possible_paths}")
    return None

# Инициализация Google Sheets
def init_google_sheets():
    global _google_sheets_client
    try:
        creds_path = get_credentials_path()
        if not creds_path:
            logger.error("Файл credentials не найден")
            return None
            
        if _google_sheets_client is None:
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
            _google_sheets_client = gspread.authorize(creds)
        
        spreadsheet = _google_sheets_client.open_by_key(SPREADSHEET_ID)
        return spreadsheet
    except Exception as e:
        logger.error(f"Ошибка инициализации Google Sheets: {e}")
        return None

# ... остальной код без изменений (функции write_to_sheet, check_google_sheets_connection, 
# start, create_request, process_defect_id, process_reason, status, help_command, cancel) ...

# Основная функция
def main() -> None:
    logger.info("="*60)
    logger.info("🤖 Запуск бота для создания заявок")
    logger.info("="*60)
    
    # Проверяем подключение к Google Sheets перед запуском
    if not check_google_sheets_connection():
        logger.warning("⚠️ Внимание: Проблемы с подключением к Google Sheets!")
        logger.warning("Бот будет работать, но заявки могут не сохраняться.")
    
    # Создаем Application
    application = Application.builder().token(TOKEN).build()
    
    # Создаем ConversationHandler
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^Создать заявку$'), create_request),
            CommandHandler('start', start)
        ],
        states={
            DEFECT_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_defect_id)
            ],
            REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_reason)
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', start)
        ],
    )
    
    # Добавляем обработчики
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help_command))
    
    # Запускаем бота
    logger.info("✅ Бот успешно запущен!")
    logger.info("📱 Напишите /start в Telegram для начала работы")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
