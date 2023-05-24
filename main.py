import asyncio
import datetime
import logging
import os
import time

import aiocron
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from dotenv import load_dotenv

import markups as nav
from db import Database

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('TOKEN', default='some_key'))
channel_id = os.getenv('CHANNEL_ID')
STRIP = os.getenv('STRIP')
UKASSA = os.getenv('UKASSA')
GROUP_URL = os.getenv('GROUP_URL')

ExistError = os.getenv('UserNotExist')

dp = Dispatcher(bot)
db = Database('database.db')


def days_to_seconds(days):
    """Перевод дней в секунды"""
    return days * 24 * 60 * 60


def time_sub_day(get_time):
    """Показывает сколько дней подписки осталось"""
    time_now = int(time.time())
    middle_time = int(get_time) - time_now
    if middle_time <= 0:
        return False
    else:
        dt = str(datetime.timedelta(seconds=middle_time))
        dt = dt.replace('days', 'дней')
        dt = dt.replace('day', 'день')
        return dt


async def check_member(channel_id: int, user_id: int):
    """Проверка есть ли пользователь в группе"""
    try:
        await bot.get_chat_member(channel_id, user_id)
        return True
    except ExistError:
        return False


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    """"Обработка команды Start, добовляем пользователя в бд,
        если его там нет"""
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id)
        await bot.send_message(message.from_user.id, 'Укажите ваш ник')
    else:
        await bot.send_message(
            message.from_user.id,
            'Вы уже зарегистрированы!',
            reply_markup=nav.mainMenu
        )


@dp.chat_join_request_handler()
async def join(update: types.ChatJoinRequest):
    """Обработка заявок на вступление в КАНАЛ и проверка присутствия
        пользователя в бд и наличие у него подписки """
    if db.user_exists(update.from_user.id) and \
            db.get_sub_status(update.from_user.id):
        await update.approve()
        await bot.send_message(
            update.from_user.id,
            text='<a href="{}">Перейти в группу</a>'.format(GROUP_URL),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
    else:
        await bot.ban_chat_member(update.chat.id, update.from_user.id)
        await asyncio.sleep(5)
        await bot.unban_chat_member(update.chat.id, update.from_user.id)
        await bot.send_photo(
            update.from_user.id,
            photo=open('static/ha-ha.jpg', 'rb'),
            caption='У вас нет подписки, вы не можете присоединяться к '
            'этому каналу!',
        )
        await bot.send_message(update.from_user.id, '/start')


async def check_subscriptions():
    """Проверка подписчиков канала, если у пользвателя подписке осталось меньше
        3х дней он получит оповещение, если подписка закончилась его кикнет из
        канала"""
    now = int(time.time())
    three_days = now + 3 * 24 * 60 * 60
    users = db.get_all_users()
    for user in users:
        user_id = user[1]
        sub_end_time = user[3]
        time_left = sub_end_time - now
        if sub_end_time < now and await check_member(channel_id, user_id):
            await bot.kick_chat_member(channel_id, user_id=user_id)
            await asyncio.sleep(5)
            await bot.unban_chat_member(channel_id, user_id=user_id)
            await bot.send_photo(
                user_id,
                photo=open('static/loh.jpg', 'rb'),
                caption='Ваша подписка закончилась!'
            )
        elif sub_end_time <= three_days and \
                await check_member(channel_id, user_id):
            days_left = int(time_left / (24 * 60 * 60))
            hours_left = int(time_left / (60 * 60) % 24)
            minutes_left = int(time_left / 60 % 60)
            message = (
                f'Вашей подписке осталось: дней {days_left} часов '
                f'{hours_left}:{minutes_left}')
            await bot.send_photo(
                user_id,
                photo=open('static/tik-tak.webp', 'rb'),
                caption=message
            )


@aiocron.crontab('00 00 * * *')  # запуск каждый день в 00:00
async def check_subscriptions_job():
    """Функция автозапуска проверки подписчиков"""
    await check_subscriptions()


@dp.message_handler()
async def bot_message(message: types.Message):

    if message.chat.type == 'private':
        if message.text == 'ПРОФИЛЬ':
            user_nickname = (
                'Ник: FIRE BEAVERS ' + db.get_nickname(message.from_user.id)
            )
            user_sub = time_sub_day(db.get_time_sub(message.from_user.id))
            if user_sub is False:
                user_sub = '\n Подписка: НЕТ'
            else:
                user_sub = '\nПодписка: ' + user_sub
            await bot.send_message(
                message.from_user.id, user_nickname + user_sub
            )
        elif message.text == 'ПОДПИСКА':
            await bot.send_message(
                message.from_user.id,
                'Описание подписки',
                reply_markup=nav.sub_inline_markup
            )
        elif message.text == 'ССЫЛКА':
            if db.get_sub_status(message.from_user.id):
                await bot.send_photo(
                    message.from_user.id,
                    photo=open('static/in_group.jpg', 'rb'),
                )
                await bot.send_message(
                    message.from_user.id,
                    text='<a href="{}">Отправить заявку</a>'.format(GROUP_URL),
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            else:
                await bot.send_photo(
                    message.from_user.id,
                    photo=open('static/plati.jpg', 'rb'),
                    caption='Купите подписку'
                )
        else:
            if db.get_signup(message.from_user.id) == 'setnickname':
                if len(message.text) > 15:
                    await bot.send_message(
                        message.from_user.id,
                        'Никнейм не должен превышать 15 символов'
                    )
                elif '@' in message.text or '/' in message.text:
                    await bot.send_message(
                        message.from_user.id,
                        'Вы ввели запрещенный символ'
                    )
                else:
                    db.set_nickname(message.from_user.id, message.text)
                    db.set_signup(message.from_user.id, 'done')
                    await bot.send_photo(
                        message.from_user.id,
                        photo=open('static/welcome.jpg', 'rb'),
                        caption='Регистрация прошла успешно!',
                        reply_markup=nav.mainMenu
                    )
            else:
                await bot.send_message(
                    message.from_user.id,
                    'Используйте кнопки, если их нет пропишите команду /start'
                )


@dp.callback_query_handler(text='submonth')
async def submonth(call: types.CallbackQuery):
    """Обработка callback-запроса, отправляем пользователю счет на оплату
        подписки на канал в USD валюте"""
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title='Oформление подписки',
        description='Подписка на канал',
        payload='month_sub',
        provider_token=STRIP,
        currency='usd',
        start_parameter='test_bot',
        prices=[{'label': 'usd', 'amount': 500}]
    )


@dp.callback_query_handler(text='submonthru')
async def submonthru(call: types.CallbackQuery):
    """Обработка callback-запроса, отправляем пользователю счет на оплату
        подписки на канал в рублях"""
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await bot.send_invoice(
        chat_id=call.from_user.id,
        title='Oформление подписки',
        description='Подписка на канал',
        payload='month_sub',
        provider_token=UKASSA,
        currency='rub',
        start_parameter='test_bot',
        prices=[{'label': 'rub', 'amount': 36000}]
    )


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(
    pre_checkout_query: types.PreCheckoutQuery
):
    """Функция обработки платежа"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
    """При успешно платеже добавляет данные об оплате в бд, и добавляет 30 дней
        подписки"""
    if message.successful_payment.invoice_payload == 'month_sub':
        db.add_payment(
            message.from_user.id,
            message.successful_payment.telegram_payment_charge_id,
            message.successful_payment.provider_payment_charge_id,
        )
        if db.get_time_sub(message.from_user.id) < int(time.time()):
            time_sub = int(time.time()) + days_to_seconds(30)
            db.set_time_sub(message.from_user.id, time_sub)
            await bot.send_photo(
                message.from_user.id,
                photo=open('static/capitalizm.jpeg', 'rb'),
                caption='Вам выдана подписка на месяц!'
            )
        else:
            time_sub = (
                db.get_time_sub(message.from_user.id) + days_to_seconds(30)
            )
            db.set_time_sub(message.from_user.id, time_sub)
            await bot.send_photo(
                message.from_user.id,
                photo=open('static/capitalizm.jpeg', 'rb'),
                caption='Вам выдана подписка на месяц!'
            )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
