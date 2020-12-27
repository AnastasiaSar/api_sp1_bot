import os
import time

import logging
import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL_HW_STATUS = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'


class TelegramHandler(logging.StreamHandler):
    def emit(self, record):
        msg = self.format(record)
        bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
        bot_client.send_message(CHAT_ID, msg)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
telegram_handler = TelegramHandler()
telegram_handler.setLevel(logging.ERROR)
logger.addHandler(telegram_handler)


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    if homework.get('status') == 'reviewing':
        return f'Работа "{homework_name}" взята в ревью'
    if homework.get('status') == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    try:
        homework_statuses = requests.get(
            URL_HW_STATUS,
            params={'from_date': current_timestamp},
            headers={'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
        )
    except requests.exceptions.RequestException as e:
        logging.error(f'Обнаружена ошибка: {e}')
    return homework_statuses.json()


def send_message(message, bot_client):
    logger.info('Отправка сообщения в телеграм')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('Запуск бота')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time()) - 3600 * 24
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(parse_homework_status(new_homework.get(
                    'homeworks')[0]),
                    bot_client
                )
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)

        except Exception as e:
            logger.error(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(5)


if __name__ == '__main__':
    main()
