import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv


load_dotenv()


logger = logging.getLogger('homework')
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
RESPONCE_OPTIONS = (
    'параметры запроса {params}, запрос по урлу: {url}, заголовок: {headers}'
)
EXCEPTION_APPEARED = 'Обнаружена ошибка: {exception}, '+RESPONCE_OPTIONS
RESPONSES = {
    'error': 'Ошибка: {error}, статус ответа: {status}, '+RESPONCE_OPTIONS,
    'code': 'Ключи ответа: {info}, статус ответа: {status}, '+RESPONCE_OPTIONS
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
    rq_pars = {'url': URL_HW_STATUS, 'params': params, 'headers': HEADERS}
    try:
        response = requests.get(**rq_pars)
    except requests.exceptions.ConnectionError as exception:
        raise ConnectionError(
            EXCEPTION_APPEARED.format(
                exception=exception,
                **rq_pars
            )
        )

    homework_statuses = response.json()
    for response in RESPONSES:
        if response in homework_statuses:
            raise RuntimeError(RESPONSES[response].format(
                response=homework_statuses[response],
                status=response.status_code,
                **rq_pars
            ))
    return homework_statuses


def send_message(message, bot_client):
    try:
        logger.info(MESSAGE.format(message=message))
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except TimeoutError:
        raise TimeoutError(RESPONSE_SEND.format(
            error=TimeoutError
            )
        )


def main():
    logger.debug(START)
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
        except Exception as all_exceptions:
            logger.error(BOT_EXCEPTION.format(exception=all_exceptions))
            time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename=__file__.replace('.py', '.log')
    )
    main()
