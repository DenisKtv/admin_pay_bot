from data import TOKEN, CHAT_ID
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types.message import ContentType
import markups as nav
import time
import datetime
import aiocron
from db import Database


logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
chat_id = CHAT_ID
YOOTOKEN = '381764678:TEST:56520'
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


@dp.message_handler(content_types=['new_chat_members'])
async def handle_new_members(message: types.Message):
    for member in message.new_chat_members:
        if db.user_exists(member.id) and db.get_sub_status(member.id):
            await bot.restrict_chat_member(
                message.chat.id, member.id, types.ChatPermissions()
            )
        else:
            await bot.ban_chat_member(message.chat.id, member.id)
            await asyncio.sleep(5)
            await bot.unban_chat_member(message.chat.id, member.id)
            await bot.send_message(
                member.id,
                'У вас нет подписки, вы не можете присоединяться к этому '
                'каналу!')


async def check_subscriptions():
    now = int(time.time())
    users = db.get_all_users()
    for user in users:
        user_id = user[1]
        sub_end_time = user[3]
        time_left = sub_end_time - now
        if time_left < now:
            await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            await asyncio.sleep(5)
            await bot.unban_chat_member(chat_id=chat_id, user_id=user_id)
            await bot.send_message(
                user_id,
                'Ваша подписка закончилась!')
        elif time_left <= datetime.timedelta(days=3).total_seconds():
            days_left = int(time_left / (24 * 60 * 60))
            hours_left = int(time_left / (60 * 60) % 24)
            minutes_left = int(time_left / 60 % 60)
            message = (f'Вашей подписке осталось: дней {days_left} '
                       f'часов {hours_left}:{minutes_left}')
            await bot.send_message(user_id, message)


@aiocron.crontab('28 21 * * *')  # запуск каждый день в 00:00
async def check_subscriptions_job():
    await check_subscriptions()


@dp.message_handler()
async def bot_message(message: types.Message):
    if message.chat.type == 'private':
        if message.text == 'ПРОФИЛЬ':
            user_nickname = 'Ваш ник: ' + db.get_nickname(message.from_user.id)
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
                await bot.send_message(message.from_user.id, 'ссылка')
            else:
                await bot.send_message(message.from_user.id, 'купите подписку')
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
                    await bot.send_message(
                        message.from_user.id,
                        'Регистрация прошла успешно!',
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
        description='Тестовое описание товара',
        payload='month_sub',
        provider_token=YOOTOKEN,
        currency='RUB',
        start_parameter='test_bot',
        prices=[{'label': 'Руб', 'amount': 15000}]
    )


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_pay(message: types.Message):
    if message.successful_payment.invoice_payload == 'month_sub':
        time_sub = int(time.time()) + days_to_seconds(30)
        db.set_time_sub(message.from_user.id, time_sub)
        await bot.send_message(
            message.from_user.id, 'вам выдана подписка на месяц!'
        )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
