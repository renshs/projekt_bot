# Импортируем необходимые классы.
import logging

import requests
from requests import get, delete
from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram.utils.request import Request
from telegram import Bot, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, bot
from telegram import ReplyKeyboardMarkup
from werkzeug.security import check_password_hash

TOKEN = '1161907381:AAFNFJ6l1UA6SZ-6QQ9XUjO9jlDQBvitXaQ'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

reply_keyboard = [['Я в магазине!']]
markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)


def del_item_from_keyboard(qry, dat):
    dat = str(dat)
    buttons_list = qry['message']['reply_markup']['inline_keyboard']
    new_buttons_list = []
    for button in buttons_list:
        if button[0]['callback_data'] != dat:
            new_buttons_list.append(button)
    return new_buttons_list


def delete_purchases(id):
    delete(f'http://09b0f307.ngrok.io/api/purchases/{id}').json()


def start(update, context):
    update.message.reply_text(
        "Здравтсвуйте, авторизируйтесь, чтобы продолжить.\nВведите логин и пароль\n'логин пароль':",
    )
    # Tell ConversationHandler that we're in state `FIRST` now
    return 1


def register(update, context):
    if ' ' in update.message.text:
        login, password = update.message.text.split()
    else:
        update.message.reply_text(
            'Вы указали неверные данные, попробуйте еще раз',
        )
    response = get('http://09b0f307.ngrok.io/api/users').json()
    found = None
    for person in response['users']:
        if person['email'] == login and check_password_hash(person['hashed_password'], password):
            found = True
            context.user_data['id'] = person['id']
            context.user_data['name'] = person['name']
    if not found:
        update.message.reply_text(
            'Вы указали неверные данные, попробуйте еще раз',
        )
    update.message.reply_text(
        f'Привет, {context.user_data["name"]}!\nКогда вы окажетесь в магазине, нажмите на кнопку и я выведу лист.',
        reply_markup=markup
    )
    return 2


def things(update, context):
    if update.message.text == 'Я в магазине!':

        resp = get('http://09b0f307.ngrok.io/api/purchases').json()
        names = []
        for item in resp['purchases']:
            if item['user_id'] == context.user_data['id']:
                name = item['title']
                count = item['count']
                purch_id = item['id']
                names.append([name, count, purch_id])
        keybrd = []
        for thing in names:
            inl_btn_name = InlineKeyboardButton(f'{thing[0]}, {thing[1]}шт.', callback_data=thing[2])
            keybrd.append([inl_btn_name])
        exit_but = InlineKeyboardButton('Завершить', callback_data='exit')
        keybrd.append([exit_but])
        reply_markup = InlineKeyboardMarkup(keybrd)

        update.message.reply_text(
            text="Ваш список:",
            reply_markup=reply_markup
        )
        return 2
    elif update.message.text == 'Выйти':
        update.message.reply_text(
            f'До свидания, {context.user_data["name"]}!'
        )

        return 1


def end(update, context):
    """Returns `ConversationHandler.END`, which tells the
    ConversationHandler that the conversation is over"""
    query = update.callback_query
    query.answer()
    query.edit_message_text(
        text="See you next time!"
    )
    return ConversationHandler.END


def ext(update, context):
    print('exit works')
    update.message.reply_text(
        f'Вы вышли из аккаунта.\nДо свидания, {context.user_data["name"]}!\nВведите логин и пароль:',
        reply_markup=ReplyKeyboardRemove()
    )
    update.message.reply_text(
        'Введите логин и пароль:',

    )
    context.user_data['id'] = None
    context.user_data['name'] = None
    return 1


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def buttons_handler(update, context):
    query = update.callback_query
    data = query.data
    chat_id = update.effective_message.chat_id
    current_text = update.effective_message.text
    if data == 'exit':
        query.edit_message_text(
            text='Всего хорошого!',
            reply_markup=InlineKeyboardMarkup([])
        )
        query.message.reply_text(
            f'Привет, {context.user_data["name"]}!'
            f'Когда вы окажетесь в магазине, нажмите на кнопку и я выведу лист.',
            reply_markup=markup
        )
        return 2
    else:
        delete_purchases(data)
        query.edit_message_text(
            text=current_text,
            reply_markup=InlineKeyboardMarkup(del_item_from_keyboard(query, data))
        )


def main():
    req = Request(
        connect_timeout=5,
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
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(Filters.text, register, pass_user_data=True)],
            2: [CommandHandler('exit', ext, pass_user_data=True),
                MessageHandler(Filters.text, things, pass_user_data=True),
                CallbackQueryHandler(callback=buttons_handler), ]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    dp.add_handler(conv_handler)

    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
