import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL_HW_STATUS = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
STATUSES = {
    'approved':
        'Ревьюеру всё понравилось, можно приступать к следующему уроку.',
    'reviewing': 'Работа "{homework}" взята в ревью',
    'rejected': 'К сожалению в работе нашлись ошибки.'
}
UNEXPECTED_STATUS = 'Неожиданный статус: {status}'
APPROVED_HOMEWORK = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
RESPONCE_OPTIONS = (
    'параметры запроса {params}, запрос по урлу: {url}, заголовок: {headers}'
)
EXCEPTION_APPEARED = (
    'Обнаружена ошибка соединения: {exception},' + RESPONCE_OPTIONS
)
RESPONSES = {
    'error': 'Ошибка: {error}, статус ответа: {status}, ' + RESPONCE_OPTIONS,
    'code': 'Ключи ответа: {code}, статус ответа: {status},' + RESPONCE_OPTIONS
}
MESSAGE = 'Отправка сообщения в телеграм: {message}'
BOT_EXCEPTION = 'Бот столкнулся с ошибкой: {exception}'
RESPONSE_SEND = 'Ошибка отправки сообщения: {error}'
START = 'Запуск бота'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}


def parse_homework_status(homework):
    name = homework['homework_name']
    status = homework['status']
    if status not in STATUSES:
        raise ValueError(UNEXPECTED_STATUS.format(status=status))
    verdict = STATUSES[status].format(homework_name=name)
    if status == 'reviewing':
        return verdict
    return APPROVED_HOMEWORK.format(
        homework_name=name,
        verdict=verdict
    )


def get_homework_statuses(current_timestamp):
    request_params = {
        'url': URL_HW_STATUS,
        'params': {'from_date': current_timestamp},
        'headers': HEADERS
    }
    try:
        response = requests.get(**request_params)
    except requests.exceptions.ConnectionError as exception:
        raise ConnectionError(
            EXCEPTION_APPEARED.format(
                exception=exception,
                **request_params
            )
        )
    response_json = response.json()
    for response_name, response_value in RESPONSES.items():
        if response_name in response_json:
            raise RuntimeError(response_value.format(
                response_name=response_value,
                status=response.status_code,
                **request_params
            ))
    return response_json


def send_message(message, bot_client):
    logger.info(MESSAGE.format(message=message))
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug(START)
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_homework_statuses(current_timestamp)
            homeworks = response.get('homeworks')
            if len(homeworks) > 0:
                send_message(parse_homework_status(homeworks[0]),
                             bot_client)
            current_timestamp = response.get(
                'current_date',
                current_timestamp
            )
            time.sleep(10)
        except Exception as all_exceptions:
            logger.error(BOT_EXCEPTION.format(exception=all_exceptions))
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=__file__.replace('.py', '.log')
    )
    main()
