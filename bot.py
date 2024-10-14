import logging
from dotenv import load_dotenv
import os
import re
import paramiko

from telegram import Update, ForceReply
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
)


load_dotenv()
TOKEN = os.getenv("TOKEN")
USER_ID = os.getenv("USER_ID")
RM_HOST = os.getenv("RM_HOST")
RM_PORT = os.getenv("RM_PORT")
RM_USER = os.getenv("RM_USER")
RM_PASSWORD = os.getenv("RM_PASSWORD")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
COMMANDS = {
    "/get_release": "lsb_release -a",
    "/get_uname": "uname -a",
    "/get_uptime": "uptime",
    "/get_df": "df",
    "/get_free": "free",
    "/get_mpstat": "mpstat",
    "/get_w": "w",
    "/get_auths": "last -n 10",
    "/get_critical": "journalctl -p err -n 5",
    "/get_ps": "ps aux",
    "/get_ss": "ss -tuln",
    "/get_services": "systemctl list-units --type=service",
}


def chunk_this(sms):
    lines = sms.splitlines()
    res, current_chunk = list(), ""

    for line in lines:
        if len(current_chunk) + len(line) + 1 <= 4096:
            current_chunk += (line + "\n") if current_chunk else line
        else:
            res.append(current_chunk)
            current_chunk = line

    if current_chunk:
        res.append(current_chunk)
    return res


def manipulate_rm_server(command: str, hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT):
    logging.info("Установка SSH соединения с сервером")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hostname, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    return data


logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)


logger = logging.getLogger(__name__)


def start(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def echo(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    update.message.reply_text(update.message.text)


def get_repl_logs(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    sms = chunk_this(manipulate_rm_server(command="tail /var/log/postgresql/postgresql-15-main.log | grep -i repl", hostname=DB_HOST, username=DB_USER, password=DB_PASSWORD, port=RM_PORT))
    for chunk in sms: update.message.reply_text(chunk)


def db_request(update: Update, context):
    TABLE_NAME = {"/get_phone_numbers": "phones", "/get_emails": "emails"}
    logging.info(f"Вызвана команда {update.message.text}")
    sms = chunk_this(manipulate_rm_server(
        f"PGPASSWORD={DB_PASSWORD} psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -c \
        'SELECT * FROM {TABLE_NAME.get(update.message.text)};'"
    ))
    for chunk in sms: update.message.reply_text(chunk)


def execute_command(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    command = COMMANDS.get(update.message.text)
    sms = chunk_this(manipulate_rm_server(command)) if command else ["Я не знаю такой команды"]
    for chunk in sms: update.message.reply_text(chunk)


def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')
    return 'findPhoneNumbers'


def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска email: ')
    return 'findEmail'


def checkPassCommand(update: Update, context):
    update.message.reply_text('Введите пароль для проверки сложности пароля: ')
    return 'checkPass'


def getAptListCommand(update: Update, context):
    update.message.reply_text('Введите название пакета или напишите all, \
                               чтобы получить информацию по всем пакетам: ')
    return 'getAptList'


def findPhoneNumbers(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    user_input = update.message.text
    phoneNumRegex = re.compile(r'(?:(?:\+7|8)[\s-]?(\(?\d{3}\)?)[\s-]?(\d{3})[\s-]?(\d{2})[\s-]?(\d{2}))')
    phoneNumberList = phoneNumRegex.findall(user_input)
    context.user_data['data'] = ["".join(i) for i in phoneNumberList]
    context.user_data["type"] = "phone"
    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    phoneNumbers = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {"".join(phoneNumberList[i])}\n'

    update.message.reply_text(phoneNumbers)
    update.message.reply_text("Хотите записать данные в БД? (y,n)")
    return 'saveInDb'


def findEmail(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    user_input = update.message.text
    emailRegex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    emailList = emailRegex.findall(user_input)
    context.user_data['data'] = emailList
    context.user_data["type"] = "email"
    if not emailList:
        update.message.reply_text('Email не найдены')
        return ConversationHandler.END
    emails = ''
    for i in range(len(emailList)):
        emails += f'{i+1}. {emailList[i]}\n'

    update.message.reply_text(emails)
    update.message.reply_text("Хотите записать данные в БД? (y,n)")
    return 'saveInDb'


def saveInDb(update: Update, context):
    data = context.user_data.get("data")
    data_type = context.user_data.get("type")
    if update.message.text == 'y':
        if data:
            values = ", ".join([f'(\'{i}\')' for i in data])
            sms = chunk_this(manipulate_rm_server(
                f'PGPASSWORD={DB_PASSWORD} psql -U {DB_USER} -h {DB_HOST} -p {DB_PORT} -c \
                "INSERT INTO {data_type}s({data_type}) VALUES {values};"'
            ))
            print(sms)
            if sms[0] == f"INSERT 0 {len(data)}":
                update.message.reply_text(f'{sms[0]}\n\nemail записаны в файл.')
            else:
                update.message.reply_text('ошибка записи в бд.')
        else:
            update.message.reply_text('ошибка записи в бд.')
    else:
        update.message.reply_text("отмена записи в бд.")

    return ConversationHandler.END


def checkPass(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    user_input = update.message.text
    pattern = r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()]).{8,}$'
    sms = "Пароль сложный" if re.match(pattern, user_input) else "Пароль простой"
    update.message.reply_text(sms)
    return ConversationHandler.END


def getAptList(update: Update, context):
    logging.info(f"Вызвана команда {update.message.text}")
    user_input = update.message.text
    packet = "--installed" if user_input == "all" else user_input
    sms_list = chunk_this(manipulate_rm_server(f"apt list {packet}"))
    for chunk in sms_list:
        update.message.reply_text(chunk)
    return ConversationHandler.END


convHandlerFindPhoneNumbers = ConversationHandler(
    entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
    states={
        'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
        'saveInDb': [MessageHandler(Filters.text & ~Filters.command, saveInDb)]
    },
    fallbacks=[]
)


convHandlerFindEmail = ConversationHandler(
    entry_points=[CommandHandler('find_email', findEmailCommand)],
    states={
        'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
        'saveInDb': [MessageHandler(Filters.text & ~Filters.command, saveInDb)]
    },
    fallbacks=[]
)


convHandlerCheckPass = ConversationHandler(
    entry_points=[CommandHandler('verify_password', checkPassCommand)],
    states={
        'checkPass': [MessageHandler(Filters.text & ~Filters.command, checkPass)],
    },
    fallbacks=[]
)


convHandlerGetAptList = ConversationHandler(
    entry_points=[CommandHandler('get_apt_list', getAptListCommand)],
    states={
        'getAptList': [MessageHandler(Filters.text & ~Filters.command, getAptList)],
    },
    fallbacks=[]
)


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("get_release", execute_command))
    dp.add_handler(CommandHandler("get_uname", execute_command))
    dp.add_handler(CommandHandler("get_uptime", execute_command))
    dp.add_handler(CommandHandler("get_df", execute_command))
    dp.add_handler(CommandHandler("get_free", execute_command))
    dp.add_handler(CommandHandler("get_mpstat", execute_command))
    dp.add_handler(CommandHandler("get_w", execute_command))
    dp.add_handler(CommandHandler("get_auths", execute_command))
    dp.add_handler(CommandHandler("get_critical", execute_command))
    dp.add_handler(CommandHandler("get_ps", execute_command))
    dp.add_handler(CommandHandler("get_ss", execute_command))
    dp.add_handler(CommandHandler("get_services", execute_command))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", db_request))
    dp.add_handler(CommandHandler("get_phone_numbers", db_request))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerCheckPass)
    dp.add_handler(convHandlerGetAptList)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
