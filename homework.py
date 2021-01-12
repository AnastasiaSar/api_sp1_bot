import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__file__)
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
INCORRECT_STATUS = 'Некорректный статус: {status}'
APPROVED_HOMEWORK = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
AUTHORIZATION = f'OAuth {PRAKTIKUM_TOKEN}'
EXCEPTION_APPEARED = (
    'Обнаружена ошибка: {exception}, параметры запроса {params}'
)
RESPONSE_ERROR = 'Ошибка: {error}, статус ответа: {status}'
RESPONSE_CODE = 'Ключи ответа: {info}, статус ответа: {status}'
MESSAGE = 'Отправка сообщения в телеграм: {message}'
BOT_EXCEPTION = 'Бот столкнулся с ошибкой: {exception}'
RESPONSE_SEND = 'Ошибка отправки сообщения: {error}'
START = 'Запуск бота'


def parse_homework_status(homework):
    print(homework)
    name = homework['homework_name']
    status = homework['status']
    if status not in STATUSES:
        raise ValueError(INCORRECT_STATUS.format(status=status))
    verdict = STATUSES[status].format(homework_name=name)
    if status == 'reviewing':
        return verdict
    return APPROVED_HOMEWORK.format(
        homework_name=name,
        verdict=verdict
    )


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            URL_HW_STATUS,
            params=params,
            headers={'Authorization': AUTHORIZATION}
        )

    except requests.exceptions.ConnectionError as exception:
        raise requests.exceptions.ConnectTimeout(
            EXCEPTION_APPEARED.format(
                exception=exception,
                params=params,
                url=URL_HW_STATUS,
                headers={'Authorization': AUTHORIZATION}
            )
        )

    status_data = response.json()
    if 'error' in status_data:
        raise RuntimeError(RESPONSE_ERROR.format(
            error=status_data['error'],
            status=response.status_code
            )
        )
    if 'code' in status_data:
        raise RuntimeError(RESPONSE_CODE.format(
            info=status_data['code'],
            status=response.status_code
            )
        )
    return status_data


def send_message(message, bot_client):
    try:
        logger.info(MESSAGE.format(message=message))
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except telegram.error.BadRequest:
        raise telegram.error.BadRequest(RESPONSE_SEND.format(
            error=telegram.error.BadRequest
            )
        )


def main():
    logger.debug(START)
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
        except Exception:
            logger.error(BOT_EXCEPTION.format(Exception=Exception))
            send_message(
                BOT_EXCEPTION.format(Exception=Exception),
                bot_client
            )
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='homework.log'
    )
    main()
