async def check_member(chat_id: int, user_id: int) -> bool:
    """Проверка есть ли пользователь в группе"""
    chat_member = await bot.get_chat_member(chat_id, user_id)
    return chat_member.status != 'left'


@dp.message_handler(content_types=['new_chat_members'])
async def handle_new_members(message: types.Message):
    """Проверка на прямое вступление в ГРУППУ, если есть подписка то впускает
        в группу, если нет, то не впускает и отправляет сообщение о том что
        надо подписаться"""
    for member in message.new_chat_members:
        if db.user_exists(member.id) and db.get_sub_status(member.id):
            await bot.restrict_chat_member(
                message.chat.id, member.id, types.ChatPermissions()
            )
        else:
            await bot.ban_chat_member(message.chat.id, member.id)
            await asyncio.sleep(5)
            await bot.unban_chat_member(message.chat.id, member.id)
            await bot.send_photo(
                member.id,
                photo=open('static/ha-ha.jpg', 'rb'),
                caption='У вас нет подписки, вы не можете присоединяться к '
                'этому каналу!',
            )
            await bot.send_message(member.id, '/start')


@dp.chat_join_request_handler()
async def join(update: types.ChatJoinRequest):
    """Обработка заявок на вступление в ГРУППУ"""
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
