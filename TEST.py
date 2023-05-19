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