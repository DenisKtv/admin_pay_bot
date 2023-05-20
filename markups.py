from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)


btnProfile = KeyboardButton('ПРОФИЛЬ')
btnSub = KeyboardButton('ПОДПИСКА')
btnGroup = KeyboardButton('ССЫЛКА')


mainMenu = ReplyKeyboardMarkup(resize_keyboard=True)
mainMenu.add(btnProfile, btnSub, btnGroup)

sub_inline_markup = InlineKeyboardMarkup(row_width=1)
btnSubMonth = InlineKeyboardButton(
    text='Месяц - 5$', callback_data='submonth'
)
btnSubMonthRu = InlineKeyboardButton(
    text='Месяц - 360rub', callback_data='submonthru'
)
sub_inline_markup.add(btnSubMonth, btnSubMonthRu)
