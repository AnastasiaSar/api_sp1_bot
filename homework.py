import os
import time

import logging
import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger(__file__ + '.log')
logger.setLevel(logging.DEBUG)
PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URL_HW_STATUS = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
STATUSES = {
    'approved': (
        'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    ),
    'reviewing': 'Работа "{homework_name}" взята в ревью',
    'rejected': 'К сожалению в работе нашлись ошибки.'
}
INCORRECT_STATUS = 'Некорректный статус: {status}'
APPROVED_HOMEWORK = 'У вас проверили работу "{homework_name}"!\n\n{verdict}'
AUTHORIZATION = f'OAuth {PRAKTIKUM_TOKEN}'
EXCEPTION_APPEARED = 'Обнаружена ошибка: {exception}, \
                      параметры запроса {params}'
RESPONSE_ERROR = 'Ошибка: {error} Ключи ответа: {info}'
MESSAGE = 'Отправка сообщения в телеграм: {message}'
BOT_EXCEPTION = 'Бот столкнулся с ошибкой: {Exception}'


def parse_homework_status(homework):
    name = homework['homework_name']
    homework_status = homework['status']
    if homework['status'] not in STATUSES:
        raise ValueError(INCORRECT_STATUS.format(status=homework_status))
    verdict = STATUSES[homework_status].format(homework_name=name)
    if homework_status == 'reviewing':
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
        print(response)

    except requests.exceptions.ConnectionError as exception:
        raise requests.exceptions.ConnectionError(
            EXCEPTION_APPEARED.format(
                exception=exception,
                params=params,
                url=response.url,
                headers=response.json()
            )
        )

    status_data = response.json()
    if 'error' in status_data and 'code' in status_data:
        raise TypeError(RESPONSE_ERROR.format(error=status_data['error'],
                                              info=status_data['code']))
    return status_data


def send_message(message, bot_client):
    logger.info(MESSAGE.format(message=message))
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logger.debug('Запуск бота')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
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
                (BOT_EXCEPTION.format(Exception=Exception)),
                bot_client
            )
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='homework.log'
    )
    main()
