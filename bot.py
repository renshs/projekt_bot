# Импортируем необходимые классы.
import logging

import requests
from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram.utils.request import Request
from telegram import Bot, ReplyKeyboardRemove
from telegram import ReplyKeyboardMarkup

TOKEN = '1161907381:AAFNFJ6l1UA6SZ-6QQ9XUjO9jlDQBvitXaQ'


def get_ll_spn(toponym):
    ll = f"{float((toponym['Point']['pos']).split()[0])},{float((toponym['Point']['pos']).split()[1])}"
    width = float(toponym['boundedBy']['Envelope']['upperCorner'].split()[0]) - float(
        toponym['boundedBy']['Envelope']['lowerCorner'].split()[0])
    height = float(toponym['boundedBy']['Envelope']['upperCorner'].split()[1]) - float(
        toponym['boundedBy']['Envelope']['lowerCorner'].split()[1])
    return ll, f"{width},{height}"


# Enable logging
def geocoder(update, context):
    print('start ')
    geocoder_uri = geocoder_request_template = "http://geocode-maps.yandex.ru/1.x/"
    response = requests.get(geocoder_uri, params={
        "apИнтеллект -9000ikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "format": "json",
        "geocode": update.message.text
    })

    toponym = response.json()["response"]["GeoObjectCollection"][
        "featureMember"][0]["GeoObject"]
    ll, spn = get_ll_spn(toponym)
    # Можно воспользоваться готовой функцией,
    # которую предлагалось сделать на уроках, посвящённых HTTP-геокодеру.
    print(ll, spn)

    static_api_request = f"http://static-maps.yandex.ru/1.x/?ll={ll}&spn={spn}&l=map"
    context.bot.send_photo(
        update.message.chat_id,  # Идентификатор чата. Куда посылать картинку.
        # Ссылка на static API, по сути, ссылка на картинку.
        # Телеграму можно передать прямо её, не скачивая предварительно карту.
        static_api_request,
        caption="Нашёл:"
    )
    print('f')


def main():
    req = Request(
        connect_timeout=0.5,
    )

    bot = Bot(
        request=req,
        token=TOKEN,
        base_url='https://telegg.ru/orig/bot'
    )

    updater = Updater(
        bot=bot,

        use_context=True,
    )
    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    # dp.add_handler(CommandHandler("geocoder", geocoder))
    text_handler = MessageHandler(Filters.text, geocoder)
    dp.add_handler(text_handler)
    # text_handler = MessageHandler(Filters.text, echo)
    #
    # dp.add_handler(text_handler)

    updater.start_polling()

    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
