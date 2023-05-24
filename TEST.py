@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
    if message.successful_payment.invoice_payload == 'month_sub':
        stripe.api_key = STRIP
        charge = stripe.Charge.create(
            amount=message.successful_payment.total_amount,
            currency=message.successful_payment.currency,
            source=message.provider_payment_charge_id,
            tg_source=message.telegram_payment_charge_id,
            description='Описание оплаты',
        )
        if charge.status == "succeeded":
            time_sub = int(time.time()) + days_to_seconds(30)
            db.set_time_sub(message.from_user.id, time_sub)
            await bot.send_message(
                message.from_user.id, 'Вам выдана подписка на месяц!'
            )
    else:
        # Обработка случая, когда платеж не соответствует условиям
        await bot.send_message(
            message.from_user.id, 'Платеж не соответствует условиям подписки.'
        )







import asyncio
import datetime
import logging
import os
import time

import aiocron
# import stripe
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
from dotenv import load_dotenv

import markups as nav
from db import Database

load_dotenv()
logging.basicConfig(level=logging.INFO)

bot = Bot(token=os.getenv('TOKEN', default='some_key'))
chat_id = os.getenv('CHAT_ID')
GROUP_URL = os.getenv('GROUP_URL')
STRIP = os.getenv('STRIP')
UKASSA = os.getenv('UKASSA')

dp = Dispatcher(bot)
db = Database('database.db')


def days_to_seconds(days):
    return days * 24 * 60 * 60


def time_sub_day(get_time):
    time_now = int(time.time())
    middle_time = int(get_time) - time_now
    if middle_time <= 0:
        return False
    else:
        dt = str(datetime.timedelta(seconds=middle_time))
        dt = dt.replace('days', 'дней')
        dt = dt.replace('day', 'день')
        return dt


async def check_member(chat_id: int, user_id: int) -> bool:
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return chat_member.status != 'left'


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if (not db.user_exists(message.from_user.id)):
        db.add_user(message.from_user.id)
        await bot.send_message(message.from_user.id, 'Укажите ваш ник')
    else:
        await bot.send_message(
            message.from_user.id,
            'Вы уже зарегистрированы!',
            reply_markup=nav.mainMenu
        )


# @dp.message_handler(content_types=['new_chat_members'])
# async def handle_new_members(message: types.Message):
#     for member in message.new_chat_members:
#         if db.user_exists(member.id) and db.get_sub_status(member.id):
#             await bot.restrict_chat_member(
#                 message.chat.id, member.id, types.ChatPermissions()
#             )
#         else:
#             await bot.ban_chat_member(message.chat.id, member.id)
#             await asyncio.sleep(5)
#             await bot.unban_chat_member(message.chat.id, member.id)
#             await bot.send_photo(
#                 member.id,
#                 photo=open('static/ha-ha.jpg', 'rb'),
#                 caption='У вас нет подписки, вы не можете присоединяться к '
#                 'этому каналу!',
#             )
#             await bot.send_message(member.id, '/start')


@dp.chat_join_request_handler()
async def join(update: types.ChatJoinRequest):
    if db.user_exists(update.from_user.id) and \
            db.get_sub_status(update.from_user.id):
        await bot.restrict_chat_member(
            chat_id, update.from_user.id, types.ChatPermissions()
        )
        await update.approve()
    else:
        await bot.ban_chat_member(chat_id, update.from_user.id)
        await asyncio.sleep(5)
        await bot.unban_chat_member(chat_id, update.from_user.id)
        await bot.send_photo(
            update.from_user.id,
            photo=open('static/ha-ha.jpg', 'rb'),
            caption='У вас нет подписки, вы не можете присоединяться к '
            'этому каналу!',
        )
        await bot.send_message(update.from_user.id, '/start')


async def check_subscriptions():
    now = int(time.time())
    three_days = now + 3 * 24 * 60 * 60
    users = db.get_all_users()
    for user in users:
        user_id = user[1]
        sub_end_time = user[3]
        time_left = sub_end_time - now
        print(time_left)
        print(now)
        if sub_end_time < now and await check_member(chat_id, user_id) is True:
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await asyncio.sleep(5)
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            await bot.send_photo(
                user_id,
                photo=open('static/loh.jpg', 'rb'),
                caption='Ваша подписка закончилась!')
        elif sub_end_time <= three_days and \
                await check_member(chat_id, user_id) is True:
            days_left = int(time_left / (24 * 60 * 60))
            hours_left = int(time_left / (60 * 60) % 24)
            minutes_left = int(time_left / 60 % 60)
            message = (f'Вашей подписке осталось: дней {days_left} '
                       f'часов {hours_left}:{minutes_left}')
            await bot.send_photo(
                user_id,
                photo=open('static/tik-tak.webp', 'rb'),
                caption=message
            )


@aiocron.crontab('35 14 * * *')  # запуск каждый день в 00:00
async def check_subscriptions_job():
    await check_subscriptions()


@dp.message_handler()
async def bot_message(message: types.Message):
    if message.chat.type == 'private':
        if message.text == 'ПРОФИЛЬ':
            user_nickname = ('Ник: FIRE BEAVERS ' +
                             db.get_nickname(message.from_user.id))
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
                    text='<a href="{}">Перейти в группу</a>'.format(GROUP_URL),
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            else:
                await bot.send_photo(
                    message.from_user.id,
                    photo=open('static/plati.jpg', 'rb'),
                    caption='Купите подписку')

        else:
            if db.get_signup(message.from_user.id) == 'setnickname':
                if (len(message.text) > 15):
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
                await bot.send_message(message.from_user.id, 'Что?')


@dp.callback_query_handler(text='submonth')
async def submonth(call: types.CallbackQuery):
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
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
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
            time_sub = (db.get_time_sub(message.from_user.id) +
                        days_to_seconds(30))
            db.set_time_sub(message.from_user.id, time_sub)
            await bot.send_photo(
                message.from_user.id,
                photo=open('static/capitalizm.jpeg', 'rb'),
                caption='Вам выдана подписка на месяц!'
            )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
