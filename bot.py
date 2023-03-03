import logging
import os
import sys
import time

import requests
import telebot
from dotenv import load_dotenv
from telebot import types

from exceptions import ApiAnswerError
from exceptions import SendMessageError

load_dotenv()
token = os.getenv('TELEGRAM_TOKEN')
bot = telebot.TeleBot(token)
TIME_SLEEP = 15
URL = 'https://yesno.wtf/api?force={answer}'

ANSWERS_DICT = {
    'Да': 'yes',
    'Нет': 'no',
    'Может быть': 'maybe',
}


@bot.message_handler(commands=['start'])
def start(message):
    """Первый запуск бота командой start."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_yes = types.KeyboardButton('Да')
    button_no = types.KeyboardButton('Нет')
    button_maybe = types.KeyboardButton('Может быть')

    markup.add(button_yes, button_no, button_maybe)

    try:
        bot.send_message(
            message.chat.id,
            'Привет, {name}. Я могу быстро искать гифки '
            'для очень важных переговоров. Для этого выбери, '
            'какая гифка-ответ тебе нужна: "Да", "Нет", "Может быть". '
            'Для удобства воспользуйтесь кнопками'.format(
                name=message.from_user.first_name
            ),
            reply_markup=markup
        )
    except SendMessageError as error:
        raise SendMessageError(f'Не отправилось приветственное '
                               f'сообщение после команды start: {error}')


def get_response(message):
    """Запрос к API."""
    try:
        response = requests.get(
            URL.format(
                answer=ANSWERS_DICT.get(
                    message.text
                )
            )
        )
    except requests.RequestException as error:
        raise ConnectionError(f'Ошибка соединения с API: {error}')
    if response.status_code != 200:
        raise ApiAnswerError(f'API недоступен, код ответа: '
                             f'{response.status_code}')
    response_json = response.json()
    if check_response(response_json) is True:
        return response_json


def check_response(response):
    """Проверка содержания ответа API."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не содержит словарь')
    if 'image' not in response:
        raise KeyError('Ответ API не содержит ключ "image"')
    if 'answer' not in response:
        raise KeyError('Ответ API не содержит ключ "answer"')
    else:
        return True


@bot.message_handler(content_types=['text'])
def send_message(message):
    """Отправка пользователю сообщения с гифкой."""
    try:
        if message.text in ANSWERS_DICT.keys():
            response = get_response(message)
            bot.send_animation(message.chat.id, response.get('image'))
        else:
            bot.send_message(message.chat.id,
                             'Я могу присылать гифки только на запросы: '
                             '"Да", "Нет",  "Может быть". Для удобства '
                             'воспользуйтесь кнопками.')
    except SendMessageError as error:
        raise SendMessageError(f'Не отправилось сообщение в ответ '
                               f'на сообщение пользователя: {error}')


def main():
    """Основная функция работы бота."""
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as error:
            logging.exception(error)
            time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(
                filename=__file__ + '.log', mode='w', encoding='UTF-8'),
            logging.StreamHandler(stream=sys.stdout)
        ],
        format='%(asctime)s, %(levelname)s, %(funcName)s, '
               '%(lineno)s, %(message)s',
    )
    main()
