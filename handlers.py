"""
Обработчики команд и сообщений бота
Вынесены отдельно для чистоты кода
"""
import time
import asyncio
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config_serverless import (
    ADMIN_CHAT_ID, ADMIN_IDS, REFERRAL_REWARD, 
    REQUIRED_CHANNELS, REQUIRED_CHANNEL_IDS,
    REQUIRED_CHANNEL, REQUIRED_CHANNEL_ID,
    NEWS_CHANNEL_ID
)

logger = logging.getLogger(__name__)

# Анти-спам
user_last_action = defaultdict(float)
SPAM_COOLDOWN = 1


# FSM состояния
class Form(StatesGroup):
    waiting_for_promocode = State()


def get_main_keyboard(is_admin=False):
    """Главная клавиатура"""
    buttons = [
        [KeyboardButton(text="⭐ Заработать звёзды")],
        [KeyboardButton(text="💰 Вывести звёзды")],
        [KeyboardButton(text="👤 Мой профиль"), KeyboardButton(text="🏆 Топ")],
        [KeyboardButton(text="🎁 Промокод")]
    ]
    
    # Добавляем кнопку статистики для админов
    if is_admin:
        buttons.append([KeyboardButton(text="📊 Статистика")])
    
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
    return keyboard


async def check_all_subscriptions(bot: Bot, user_id: int) -> tuple[bool, list]:
    """Проверка подписки на все обязательные каналы"""
    not_subscribed = []
    
    for channel_id, channel_username in zip(REQUIRED_CHANNEL_IDS, REQUIRED_CHANNELS):
        try:
            logger.info(f"Checking subscription for user {user_id} in channel {channel_id}")
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            logger.info(f"User {user_id} status in channel {channel_username}: {member.status}")
            
            if member.status not in ['member', 'administrator', 'creator']:
                not_subscribed.append((channel_username, channel_id))
        except Exception as e:
            logger.error(f"Error checking subscription for {user_id} in {channel_id}: {e}")
            not_subscribed.append((channel_username, channel_id))
    
    is_fully_subscribed = len(not_subscribed) == 0
    logger.info(f"User {user_id} full subscription check: {is_fully_subscribed}")
    
    return is_fully_subscribed, not_subscribed


async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Проверка подписки на обязательный канал (для обратной совместимости)"""
    is_subscribed, _ = await check_all_subscriptions(bot, user_id)
    return is_subscribed


def get_subscription_keyboard(not_subscribed_channels=None):
    """Клавиатура с кнопками подписки"""
    if not_subscribed_channels:
        # Кнопки для каждого канала
        buttons = []
        for channel_username, _ in not_subscribed_channels:
            buttons.append([InlineKeyboardButton(
                text=f"📢 Подписаться на {channel_username}", 
                url=f"https://t.me/{channel_username.lstrip('@')}"
            )])
        buttons.append([InlineKeyboardButton(text="✅ Я подписался на все каналы!", callback_data="check_subscription")])
    else:
        # Старый формат для одного канала
        buttons = [
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=f"https://t.me/{REQUIRED_CHANNEL.lstrip('@')}")],
            [InlineKeyboardButton(text="✅ Я подписался!", callback_data="check_subscription")]
        ]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def is_admin(user_id: int) -> bool:
    """Проверка на админа"""
    return user_id in ADMIN_IDS


def is_real_user(user: types.User) -> bool:
    """Проверка на бота"""
    if user.is_bot:
        logger.warning(f"Bot attempt: {user.id}")
        return False
    if user.id > 9999999999:
        logger.warning(f"Suspicious ID: {user.id}")
        return False
    return True


def register_handlers(dp: Dispatcher, bot: Bot, db):
    """Регистрация всех обработчиков"""
    
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        """Команда /start"""
        user_id = message.from_user.id
        username = message.from_user.username or "Без username"
        full_name = message.from_user.full_name
        
        if not is_real_user(message.from_user):
            return
        
        current_time = time.time()
        if current_time - user_last_action[user_id] < SPAM_COOLDOWN:
            return
        user_last_action[user_id] = current_time
        
        command_text = message.text
        logger.info(f"Start command from {user_id}: {command_text}")
        
        # Парсим реферальный параметр
        referrer_id = None
        if ' ' in command_text:
            try:
                ref_param = command_text.split(' ', 1)[1].strip()
                referrer_id = int(ref_param)
                logger.info(f"Referrer detected: {referrer_id}")
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing referrer: {e}")
        
        user_exists = db.user_exists(user_id)
        logger.info(f"User {user_id} exists: {user_exists}")
        
        # Регистрируем пользователя, если не существует
        if not user_exists:
            db.add_user(user_id, username, full_name, referrer_id)
            logger.info(f"New user {user_id} registered with referrer {referrer_id}")
        
        # Проверка подписки на все каналы
        is_subscribed, not_subscribed = await check_all_subscriptions(bot, user_id)
        
        if not is_subscribed:
            channels_text = "\n".join([f"• {ch}" for ch, _ in not_subscribed])
            await message.answer(
                f"👋 Привет, {full_name}!\n\n"
                f"🔒 Для использования бота необходимо подписаться на наши каналы:\n\n"
                f"{channels_text}\n\n"
                f"После подписки нажми кнопку '✅ Я подписался на все каналы!'",
                reply_markup=get_subscription_keyboard(not_subscribed)
            )
            return
        
        # Начисляем награду рефереру только после подписки
        if referrer_id and referrer_id != user_id and not user_exists:
            referrer_exists = db.user_exists(referrer_id)
            
            if referrer_exists:
                try:
                    referrer_info = await bot.get_chat(referrer_id)
                    if referrer_info.type == 'private':
                        db.add_balance(referrer_id, REFERRAL_REWARD)
                        db.increment_referral_count(referrer_id)
                        
                        try:
                            await bot.send_message(
                                referrer_id,
                                f"🎉 По вашей ссылке зарегистрировался и подписался новый друг!\n"
                                f"Вам начислено +{REFERRAL_REWARD} ⭐\n\n"
                                f"👤 Новый реферал: {full_name}"
                            )
                            logger.info(f"Referral reward sent to {referrer_id}")
                        except Exception as e:
                            logger.error(f"Failed to notify referrer {referrer_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing referrer {referrer_id}: {e}")
        
        await message.answer(
            f"✨ Добро пожаловать, {full_name}!\n\n"
            "🌟 Реферальный бот для заработка Звёзд!\n\n"
            f"Приглашай друзей по своей реферальной ссылке и получай +{REFERRAL_REWARD} ⭐ за каждого!\n\n"
            f"⚠️ Награда начисляется только после подписки друга на все каналы.",
            reply_markup=get_main_keyboard(is_admin(user_id))
        )
    
    
    @dp.message(F.text.in_(["⭐ Заработать звёзды", "💰 Вывести звёзды", "👤 Мой профиль", "🎁 Промокод", "📊 Статистика", "🏆 Топ"]))
    async def handle_menu_buttons(message: types.Message, state: FSMContext):
        """Обработка кнопок меню"""
        user_id = message.from_user.id
        
        if not is_real_user(message.from_user):
            return
        
        current_time = time.time()
        if current_time - user_last_action[user_id] < SPAM_COOLDOWN:
            await message.answer("⏳ Пожалуйста, подождите немного.")
            return
        user_last_action[user_id] = current_time
        
        # Статистика доступна только админам без проверки подписки
        if message.text == "📊 Статистика":
            if is_admin(user_id):
                await show_stats(message, db)
            return
        
        # Топ доступен всем без проверки подписки
        if message.text == "🏆 Топ":
            await show_top(message, db)
            return
        
        # Проверка подписки на все каналы
        is_subscribed, not_subscribed = await check_all_subscriptions(bot, user_id)
        if not is_subscribed:
            channels_text = "\n".join([f"• {ch}" for ch, _ in not_subscribed])
            await message.answer(
                f"🔒 Для использования бота необходимо подписаться на все наши каналы:\n\n"
                f"{channels_text}\n\n"
                f"После подписки нажми кнопку '✅ Я подписался на все каналы!'",
                reply_markup=get_subscription_keyboard(not_subscribed)
            )
            return
        
        if message.text == "⭐ Заработать звёзды":
            await earn_stars(message, bot, db)
        elif message.text == "💰 Вывести звёзды":
            await withdraw_stars(message)
        elif message.text == "👤 Мой профиль":
            await my_profile(message, db)
        elif message.text == "🎁 Промокод":
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
                ]
            )
            await message.answer(
                "🎁 <b>Активация промокода</b>\n\n"
                "Введите промокод:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            await state.set_state(Form.waiting_for_promocode)
    
    
    async def show_top(message: types.Message, db):
        """Показать топ рефереров"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🏆 За всё время", callback_data="top_alltime"),
                    InlineKeyboardButton(text="📅 За неделю", callback_data="top_week")
                ]
            ]
        )
        
        await message.answer(
            "🏆 <b>Топ рефереров</b>\n\n"
            "Выберите период:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    
    async def show_stats(message: types.Message, db):
        """Показать статистику (для админов)"""
        try:
            stats = db.get_statistics()
            
            # Подсчитываем общую сумму выведенных звёзд
            total_earned = stats['total_referrals'] * REFERRAL_REWARD
            
            await message.answer(
                f"📊 <b>Статистика бота</b>\n\n"
                f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
                f"💰 Звёзд в обороте: <b>{stats['total_balance']:.1f} ⭐</b>\n"
                f"🔗 Всего рефералов: <b>{stats['total_referrals']}</b>\n"
                f"💸 Выдано за рефералов: <b>{total_earned:.1f} ⭐</b>\n\n"
                
                f"📋 <b>Заявки на вывод:</b>\n"
                f"🔴 Открытых: <b>{stats['pending_withdrawals']}</b> ({stats['pending_amount']:.1f} ⭐)\n"
                f"✅ Закрытых: <b>{stats['completed_withdrawals']}</b> ({stats['completed_amount']:.1f} ⭐)\n"
                f"📊 Всего заявок: <b>{stats['total_withdrawals']}</b>\n"
                f"💵 Всего запрошено: <b>{stats['total_withdrawn']:.1f} ⭐</b>\n\n"
                
                f"📈 <b>Средние показатели:</b>\n"
                f"💰 Средний баланс: <b>{stats['total_balance'] / max(stats['total_users'], 1):.1f} ⭐</b>\n"
                f"👤 Среднее рефералов: <b>{stats['total_referrals'] / max(stats['total_users'], 1):.1f}</b>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
            await message.answer(f"❌ Ошибка получения статистики: {e}")
    
    
    async def earn_stars(message: types.Message, bot: Bot, db):
        """Заработать звёзды"""
        user_id = message.from_user.id
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start={user_id}"
        
        user_data = db.get_user(user_id)
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
            ]
        )
        
        await message.answer(
            f"💫 <b>Заработать Звёзды</b>\n\n"
            f"За каждого друга, который перейдет по твоей ссылке, ты получаешь <b>+{REFERRAL_REWARD} ⭐</b>!\n\n"
            f"📊 Твоя статистика:\n"
            f"👥 Приглашено друзей: {user_data['referral_count']}\n"
            f"💰 Заработано всего: {user_data['referral_count'] * REFERRAL_REWARD} ⭐\n\n"
            f"📎 Твоя реферальная ссылка:\n"
            f"<code>{ref_link}</code>\n\n"
            f"<i>Нажми на ссылку, чтобы скопировать</i>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    
    async def withdraw_stars(message: types.Message):
        """Вывести звёзды"""
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="15 ⭐", callback_data="withdraw_15"),
                    InlineKeyboardButton(text="25 ⭐", callback_data="withdraw_25")
                ],
                [
                    InlineKeyboardButton(text="50 ⭐", callback_data="withdraw_50"),
                    InlineKeyboardButton(text="100 ⭐", callback_data="withdraw_100")
                ],
                [
                    InlineKeyboardButton(text="🌟 TELEGRAM PREMIUM (350 ⭐)", callback_data="withdraw_350")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")
                ]
            ]
        )
        
        await message.answer(
            "💰 <b>Вывести звёзды</b>\n\n"
            "Выбери количество звёзд, которое хочешь вывести:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    
    async def my_profile(message: types.Message, db):
        """Мой профиль"""
        user_id = message.from_user.id
        user_data = db.get_user(user_id)
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_menu")]
            ]
        )
        
        await message.answer(
            f"👤 <b>Мой профиль</b>\n\n"
            f"📝 Имя: {user_data['full_name']}\n"
            f"🆔 ID: <code>{user_id}</code>\n"
            f"💰 Баланс: {user_data['balance']} ⭐\n"
            f"👥 Приглашено друзей: {user_data['referral_count']}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    
    @dp.callback_query(F.data == "check_subscription")
    async def check_subscription_callback(callback: types.CallbackQuery):
        """Проверка подписки по кнопке"""
        user_id = callback.from_user.id
        full_name = callback.from_user.full_name
        
        is_subscribed, not_subscribed = await check_all_subscriptions(bot, user_id)
        
        if is_subscribed:
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Failed to delete message: {e}")
            
            # Проверяем, новый ли это пользователь с рефералом
            user_data = db.get_user(user_id)
            referrer_id = user_data.get('referrer_id') if user_data else None
            
            # Если есть реферер и он еще не получил награду (проверяем по базе)
            if referrer_id and referrer_id != user_id:
                # Проверяем, была ли уже начислена награда
                # (это защита от повторного начисления при отписке/подписке)
                if user_data and user_data.get('referral_count') == 0:
                    # Пользователь только что подписался, начисляем награду рефереру
                    try:
                        db.add_balance(referrer_id, REFERRAL_REWARD)
                        db.increment_referral_count(referrer_id)
                        
                        await bot.send_message(
                            referrer_id,
                            f"🎉 По вашей ссылке зарегистрировался и подписался новый друг!\n"
                            f"Вам начислено +{REFERRAL_REWARD} ⭐\n\n"
                            f"👤 Новый реферал: {full_name}"
                        )
                        logger.info(f"Referral reward sent to {referrer_id} for user {user_id}")
                    except Exception as e:
                        logger.error(f"Error rewarding referrer {referrer_id}: {e}")
            
            await callback.message.answer(
                f"✅ Отлично! Вы подписаны на все каналы!\n\n"
                f"✨ Теперь вы можете пользоваться ботом!\n\n"
                f"Приглашай друзей и получай +{REFERRAL_REWARD} ⭐ за каждого!\n"
                f"⚠️ Награда начисляется только после подписки друга на все каналы.",
                reply_markup=get_main_keyboard(is_admin(user_id))
            )
            await callback.answer("✅ Подписка подтверждена!", show_alert=False)
        else:
            channels_text = ", ".join([ch for ch, _ in not_subscribed])
            await callback.answer(
                f"❌ Вы ещё не подписались на все каналы!\n\n"
                f"Не хватает: {channels_text}\n\n"
                f"Подпишитесь и нажмите кнопку снова!",
                show_alert=True
            )
    
    
    @dp.callback_query(F.data == "top_alltime")
    async def top_alltime_callback(callback: types.CallbackQuery):
        """Топ за всё время"""
        try:
            top_users = db.get_top_referrers_alltime(10)
            
            if not top_users:
                await callback.message.edit_text(
                    "🏆 <b>Топ за всё время</b>\n\n"
                    "Пока никто не пригласил друзей.\n"
                    "Станьте первым! 🚀",
                    parse_mode="HTML"
                )
                await callback.answer()
                return
            
            text = "🏆 <b>Топ за всё время</b>\n\n"
            medals = ["🥇", "🥈", "🥉"]
            
            for i, user in enumerate(top_users, 1):
                medal = medals[i-1] if i <= 3 else f"{i}."
                name = user['full_name']
                count = user['referral_count']
                
                # Обрезаем длинные имена
                if len(name) > 20:
                    name = name[:20] + "..."
                
                text += f"{medal} {name} — <b>{count}</b> реф.\n"
            
            text += f"\n💰 Награда за реферала: <b>{REFERRAL_REWARD} ⭐</b>"
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🏆 За всё время", callback_data="top_alltime"),
                        InlineKeyboardButton(text="📅 За неделю", callback_data="top_week")
                    ]
                ]
            )
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        except Exception as e:
            logger.error(f"Error showing top alltime: {e}")
            await callback.answer("❌ Ошибка загрузки топа", show_alert=True)
    
    
    @dp.callback_query(F.data == "top_week")
    async def top_week_callback(callback: types.CallbackQuery):
        """Топ за неделю"""
        try:
            top_users = db.get_top_referrers_week(10)
            
            if not top_users:
                await callback.message.edit_text(
                    "📅 <b>Топ за неделю</b>\n\n"
                    "За последние 7 дней никто не пригласил друзей.\n"
                    "Станьте первым! 🚀\n\n"
                    "🎁 <b>Скоро:</b> Победители недели получат NFT!",
                    parse_mode="HTML"
                )
                await callback.answer()
                return
            
            text = "📅 <b>Топ за неделю</b>\n\n"
            medals = ["🥇", "🥈", "🥉"]
            
            for i, user in enumerate(top_users, 1):
                medal = medals[i-1] if i <= 3 else f"{i}."
                name = user['full_name']
                count = user['weekly_referrals']
                
                # Обрезаем длинные имена
                if len(name) > 20:
                    name = name[:20] + "..."
                
                text += f"{medal} {name} — <b>{count}</b> реф.\n"
            
            text += f"\n💰 Награда за реферала: <b>{REFERRAL_REWARD} ⭐</b>\n"
            text += f"🎁 <b>Скоро:</b> Победители недели получат NFT!"
            
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="🏆 За всё время", callback_data="top_alltime"),
                        InlineKeyboardButton(text="📅 За неделю", callback_data="top_week")
                    ]
                ]
            )
            
            await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
            await callback.answer()
        except Exception as e:
            logger.error(f"Error showing top week: {e}")
            await callback.answer("❌ Ошибка загрузки топа", show_alert=True)
    
    
    @dp.callback_query(F.data.startswith("withdraw_"))
    async def process_withdrawal(callback: types.CallbackQuery):
        """Обработка вывода"""
        user_id = callback.from_user.id
        
        if not is_real_user(callback.from_user):
            return
        
        current_time = time.time()
        if current_time - user_last_action[user_id] < SPAM_COOLDOWN:
            await callback.answer("⏳ Пожалуйста, подождите.", show_alert=True)
            return
        user_last_action[user_id] = current_time
        
        amount = int(callback.data.split("_")[1])
        user_data = db.get_user(user_id)
        current_balance = user_data['balance']
        
        if current_balance >= amount:
            db.subtract_balance(user_id, amount)
            withdrawal_id = db.create_withdrawal(user_id, amount)
            
            username = callback.from_user.username
            full_name = callback.from_user.full_name
            
            # Формируем ссылку на пользователя
            if username:
                user_link = f"@{username}"
            else:
                # Кликабельная ссылка на профиль через ID (работает даже без username)
                user_link = f'<a href="tg://user?id={user_id}">{full_name}</a>'
            
            admin_message = (
                f"📤 <b>Новая заявка на вывод</b>\n\n"
                f"👤 Пользователь: {user_link}\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"💰 Сумма: {amount} ⭐\n"
                f"📊 Рефералов: {user_data['referral_count']}\n"
            )
            
            if amount == 350:
                admin_message += f"\n🎁 <b>TELEGRAM PREMIUM</b>"
            
            # Кнопка для подтверждения выдачи
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Выдано", callback_data=f"complete_withdrawal_{withdrawal_id}")]
                ]
            )
            
            # Отправляем уведомление всем админам и сохраняем message_id
            for admin_id in ADMIN_IDS:
                try:
                    msg = await bot.send_message(admin_id, admin_message, reply_markup=keyboard, parse_mode="HTML")
                    # Сохраняем ID сообщения для синхронизации
                    db.save_withdrawal_message(withdrawal_id, admin_id, msg.message_id)
                    logger.info(f"Withdrawal request sent to admin {admin_id}, message_id: {msg.message_id}")
                except Exception as e:
                    logger.error(f"Error sending withdrawal to admin {admin_id}: {e}")
            
            await callback.answer("✅ Заявка на вывод успешно создана!", show_alert=True)
            await callback.message.answer(
                f"✅ Заявка на вывод <b>{amount} ⭐</b> успешно создана!\n\n"
                f"💰 Ваш баланс: {current_balance - amount} ⭐\n"
                f"Ожидайте обработки администратором.",
                parse_mode="HTML"
            )
        else:
            await callback.answer(
                f"❌ Недостаточно звёзд!\nТребуется: {amount} ⭐\nУ вас: {current_balance} ⭐",
                show_alert=True
            )
    
    
    @dp.callback_query(F.data.startswith("complete_withdrawal_"))
    async def complete_withdrawal_callback(callback: types.CallbackQuery):
        """Подтверждение выдачи звёзд"""
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Только для админов!", show_alert=True)
            return
        
        try:
            withdrawal_id = int(callback.data.split("_")[2])
            admin_id = callback.from_user.id
            
            # Получаем информацию о заявке
            withdrawal = db.get_withdrawal(withdrawal_id)
            
            if not withdrawal:
                await callback.answer("❌ Заявка не найдена", show_alert=True)
                return
            
            if withdrawal['status'] == 'completed':
                await callback.answer("✅ Заявка уже обработана", show_alert=True)
                return
            
            # Отмечаем как выполненную
            db.complete_withdrawal(withdrawal_id, admin_id)
            
            # Получаем оригинальный текст
            original_text = callback.message.text or callback.message.caption
            
            # Формируем обновлённый текст
            updated_text = original_text + f"\n\n✅ <b>Выдано</b> админом <code>{admin_id}</code>"
            
            # Получаем все сообщения этой заявки у всех админов
            messages = db.get_withdrawal_messages(withdrawal_id)
            
            # Обновляем сообщения у ВСЕХ админов
            for msg_data in messages:
                try:
                    await bot.edit_message_text(
                        chat_id=msg_data['admin_id'],
                        message_id=msg_data['message_id'],
                        text=updated_text,
                        parse_mode="HTML"
                    )
                    logger.info(f"Updated withdrawal message for admin {msg_data['admin_id']}")
                except Exception as e:
                    logger.error(f"Failed to update message for admin {msg_data['admin_id']}: {e}")
            
            await callback.answer("✅ Заявка отмечена как выполненная у всех админов!", show_alert=True)
            logger.info(f"Withdrawal {withdrawal_id} completed by admin {admin_id}")
            
        except Exception as e:
            logger.error(f"Error completing withdrawal: {e}")
            await callback.answer("❌ Ошибка обработки заявки", show_alert=True)
    
    
    @dp.message(Form.waiting_for_promocode)
    async def process_promocode(message: types.Message, state: FSMContext):
        """Обработка промокода"""
        user_id = message.from_user.id
        
        if not is_real_user(message.from_user):
            await state.clear()
            return
        
        current_time = time.time()
        if current_time - user_last_action[user_id] < SPAM_COOLDOWN:
            await message.answer("⏳ Пожалуйста, подождите.")
            return
        user_last_action[user_id] = current_time
        
        promo_code = message.text.strip().upper()
        
        if len(promo_code) < 3 or len(promo_code) > 50:
            await message.answer(
                "❌ Неверный формат промокода!\n"
                "Промокод должен содержать от 3 до 50 символов.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        if not promo_code.replace('_', '').replace('-', '').isalnum():
            await message.answer(
                "❌ Промокод может содержать только буквы, цифры, дефис и подчёркивание.",
                reply_markup=get_main_keyboard()
            )
            await state.clear()
            return
        
        result = db.activate_promocode(user_id, promo_code)
        
        if result['success']:
            await message.answer(
                f"✅ <b>Промокод успешно активирован!</b>\n\n"
                f"💰 Вам начислено <b>{result['amount']} ⭐</b>",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"❌ <b>Ошибка активации промокода</b>\n\n"
                f"{result['message']}",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        
        await state.clear()
    
    
    @dp.callback_query(F.data == "back_to_menu")
    async def back_to_menu(callback: types.CallbackQuery):
        """Возврат в меню"""
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Failed to delete message: {e}")
        
        await callback.message.answer(
            "✨ Главное меню",
            reply_markup=get_main_keyboard(is_admin(callback.from_user.id))
        )
    
    
    # Админ команды
    @dp.message(Command("create_promo"))
    async def create_promocode_command(message: types.Message):
        """Создание промокода"""
        if not is_admin(message.from_user.id):
            return
        
        try:
            parts = message.text.split()
            if len(parts) != 3:
                await message.answer(
                    "❌ Неверный формат!\n"
                    "Используйте: /create_promo <код> <сумма>\n"
                    "Пример: /create_promo BONUS100 100"
                )
                return
            
            promo_code = parts[1].upper()
            amount = float(parts[2])
            
            if amount <= 0:
                await message.answer("❌ Сумма должна быть положительной!")
                return
            
            db.create_promocode(promo_code, amount)
            
            await message.answer(
                f"✅ Промокод создан!\n\n"
                f"🎁 Код: <code>{promo_code}</code>\n"
                f"💰 Сумма: {amount} ⭐",
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    
    
    @dp.message(Command("check_user"))
    async def check_user_command(message: types.Message):
        """Проверка пользователя"""
        if not is_admin(message.from_user.id):
            return
        
        try:
            parts = message.text.split()
            if len(parts) != 2:
                await message.answer(
                    "❌ Неверный формат!\n"
                    "Используйте: /check_user <user_id>"
                )
                return
            
            check_id = int(parts[1])
            user_data = db.get_user(check_id)
            
            if user_data:
                await message.answer(
                    f"👤 <b>Информация о пользователе</b>\n\n"
                    f"🆔 ID: <code>{user_data['user_id']}</code>\n"
                    f"📝 Username: {user_data['username']}\n"
                    f"👤 Имя: {user_data['full_name']}\n"
                    f"💰 Баланс: {user_data['balance']} ⭐\n"
                    f"👥 Рефералов: {user_data['referral_count']}\n"
                    f"🔗 Пригласил: {user_data['referrer_id'] or 'Никто'}",
                    parse_mode="HTML"
                )
            else:
                await message.answer(f"❌ Пользователь не найден")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    
    
    @dp.message(Command("stats"))
    async def stats_command(message: types.Message):
        """Статистика"""
        if not is_admin(message.from_user.id):
            return
        
        await show_stats(message, db)
    
    
    @dp.message(Command("set_balance"))
    async def set_balance_command(message: types.Message):
        """Установить баланс"""
        if not is_admin(message.from_user.id):
            return
        
        try:
            parts = message.text.split()
            if len(parts) != 3:
                await message.answer(
                    "❌ Неверный формат!\n"
                    "Используйте: /set_balance <user_id> <сумма>"
                )
                return
            
            target_user_id = int(parts[1])
            new_balance = float(parts[2])
            
            user_data = db.get_user(target_user_id)
            if not user_data:
                await message.answer(f"❌ Пользователь не найден")
                return
            
            old_balance = user_data['balance']
            db.set_balance(target_user_id, new_balance)
            
            await message.answer(
                f"✅ <b>Баланс обновлён</b>\n\n"
                f"👤 Пользователь: {user_data['full_name']}\n"
                f"💰 Было: {old_balance} ⭐\n"
                f"💰 Стало: {new_balance} ⭐",
                parse_mode="HTML"
            )
            
            try:
                await bot.send_message(
                    target_user_id,
                    f"💰 <b>Ваш баланс был скорректирован</b>\n\n"
                    f"Новый баланс: {new_balance} ⭐",
                    parse_mode="HTML"
                )
            except:
                pass
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    
    
    @dp.message(Command("add_balance"))
    async def add_balance_command(message: types.Message):
        """Добавить к балансу"""
        if not is_admin(message.from_user.id):
            return
        
        try:
            parts = message.text.split()
            if len(parts) != 3:
                await message.answer(
                    "❌ Неверный формат!\n"
                    "Используйте: /add_balance <user_id> <сумма>"
                )
                return
            
            target_user_id = int(parts[1])
            amount = float(parts[2])
            
            user_data = db.get_user(target_user_id)
            if not user_data:
                await message.answer(f"❌ Пользователь не найден")
                return
            
            old_balance = user_data['balance']
            db.add_balance(target_user_id, amount)
            new_balance = old_balance + amount
            
            await message.answer(
                f"✅ <b>Баланс обновлён</b>\n\n"
                f"👤 Пользователь: {user_data['full_name']}\n"
                f"💰 Было: {old_balance} ⭐\n"
                f"➕ Добавлено: {amount} ⭐\n"
                f"💰 Стало: {new_balance} ⭐",
                parse_mode="HTML"
            )
            
            try:
                await bot.send_message(
                    target_user_id,
                    f"🎁 <b>Вам начислены бонусные звёзды!</b>\n\n"
                    f"Начислено: +{amount} ⭐\n"
                    f"Ваш баланс: {new_balance} ⭐",
                    parse_mode="HTML"
                )
            except:
                pass
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    
    
    @dp.message(Command("check_channel"))
    async def check_channel_command(message: types.Message):
        """Проверка подключения к каналу (для отладки)"""
        if not is_admin(message.from_user.id):
            return
        
        try:
            # Пробуем получить информацию о канале
            chat = await bot.get_chat(REQUIRED_CHANNEL_ID)
            
            # Проверяем статус бота в канале
            bot_member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=bot.id)
            
            await message.answer(
                f"📊 <b>Информация о канале</b>\n\n"
                f"🆔 ID канала: <code>{REQUIRED_CHANNEL_ID}</code>\n"
                f"📝 Название: {chat.title}\n"
                f"👤 Username: {chat.username or 'Нет'}\n"
                f"🤖 Статус бота: {bot_member.status}\n\n"
                f"✅ Бот подключён к каналу правильно!",
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer(
                f"❌ <b>Ошибка подключения к каналу</b>\n\n"
                f"🆔 ID канала: <code>{REQUIRED_CHANNEL_ID}</code>\n"
                f"📝 Username: {REQUIRED_CHANNEL}\n"
                f"❗ Ошибка: {str(e)}\n\n"
                f"<b>Возможные причины:</b>\n"
                f"• Неправильный ID канала\n"
                f"• Бот не добавлен администратором в канал\n"
                f"• Канал не существует",
                parse_mode="HTML"
            )
    
    
    @dp.message(Command("test_sub"))
    async def test_subscription_command(message: types.Message):
        """Проверка подписки текущего пользователя (для отладки)"""
        user_id = message.from_user.id
        
        try:
            is_subscribed = await check_subscription(bot, user_id)
            
            if is_subscribed:
                await message.answer(
                    f"✅ Вы подписаны на канал!\n\n"
                    f"🆔 Ваш ID: <code>{user_id}</code>\n"
                    f"📢 Канал: {REQUIRED_CHANNEL}",
                    parse_mode="HTML"
                )
            else:
                member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
                await message.answer(
                    f"❌ Вы НЕ подписаны на канал\n\n"
                    f"🆔 Ваш ID: <code>{user_id}</code>\n"
                    f"📢 Канал: {REQUIRED_CHANNEL}\n"
                    f"📊 Ваш статус: {member.status}",
                    parse_mode="HTML"
                )
        except Exception as e:
            await message.answer(
                f"❌ Ошибка проверки подписки\n\n"
                f"🆔 ID канала: <code>{REQUIRED_CHANNEL_ID}</code>\n"
                f"❗ Ошибка: {str(e)}",
                parse_mode="HTML"
            )
    
    
    @dp.message(Command("test_news"))
    async def test_news_command(message: types.Message):
        """Тестирование системы новостей (только для админов)"""
        if not is_admin(message.from_user.id):
            return
        
        await message.answer(
            f"📊 <b>Конфигурация новостей:</b>\n\n"
            f"🆔 NEWS_CHANNEL_ID: <code>{NEWS_CHANNEL_ID}</code>\n"
            f"📢 Канал: @nebula_starsc\n\n"
            f"<b>Инструкция:</b>\n"
            f"1. Опубликуйте пост в канале с хэштегом #новости\n"
            f"2. Бот должен разослать его всем пользователям\n"
            f"3. Вы получите отчёт о рассылке\n\n"
            f"<b>Проверьте:</b>\n"
            f"• Бот добавлен админом в канал\n"
            f"• ID канала правильный\n"
            f"• Вебхук переустановлен (/set_webhook)",
            parse_mode="HTML"
        )
    
    
    # Обработчик постов из канала с хэштегом #новости
    @dp.channel_post()
    async def handle_channel_post(message: types.Message):
        """Обработка постов из канала для рассылки новостей"""
        try:
            # Проверяем, что пост из нужного канала
            if message.chat.id != NEWS_CHANNEL_ID:
                logger.info(f"Channel post from {message.chat.id}, expected {NEWS_CHANNEL_ID}, skipping")
                return
            
            logger.info(f"Channel post from correct channel {NEWS_CHANNEL_ID}")
            
            # Проверяем наличие хэштега #новости
            if not message.text and not message.caption:
                logger.info("No text or caption in channel post, skipping")
                return
            
            text_to_check = message.text or message.caption or ""
            logger.info(f"Channel post text: {text_to_check[:100]}...")
            
            if "#новости" not in text_to_check.lower():
                logger.info("No #новости hashtag found, skipping")
                return
            
            logger.info(f"News post detected from channel {NEWS_CHANNEL_ID}, starting broadcast")
            
            # Получаем всех пользователей из базы
            try:
                with db.get_cursor() as cursor:
                    cursor.execute("SELECT user_id FROM users")
                    users = cursor.fetchall()
                logger.info(f"Found {len(users)} users for broadcast")
            except Exception as e:
                logger.error(f"Failed to get users from database: {e}")
                return
            
            # Счётчики успешных/неудачных отправок
            success_count = 0
            fail_count = 0
            
            # Отправляем новость всем пользователям
            for user in users:
                user_id = user[0]
                try:
                    await message.forward(user_id)
                    success_count += 1
                    await asyncio.sleep(0.05)  # Небольшая задержка между отправками
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Failed to send news to user {user_id}: {e}")
            
            logger.info(f"News broadcast completed: {success_count} success, {fail_count} failed")
            
            # Отправляем отчет админам
            report = (
                f"📰 <b>Рассылка новостей завершена</b>\n\n"
                f"✅ Успешно отправлено: {success_count}\n"
                f"❌ Не удалось отправить: {fail_count}\n"
                f"👥 Всего пользователей: {len(users)}"
            )
            
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, report, parse_mode="HTML")
                    logger.info(f"Report sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send report to admin {admin_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in news broadcast: {e}")
    
    
    # Обработчик РЕДАКТИРОВАННЫХ постов из канала с хэштегами #новости и #upd
    @dp.edited_channel_post()
    async def handle_edited_channel_post(message: types.Message):
        """Обработка отредактированных постов из канала для повторной рассылки"""
        try:
            # Проверяем, что пост из нужного канала
            if message.chat.id != NEWS_CHANNEL_ID:
                logger.info(f"Edited channel post from {message.chat.id}, expected {NEWS_CHANNEL_ID}, skipping")
                return
            
            logger.info(f"Edited channel post from correct channel {NEWS_CHANNEL_ID}")
            
            # Проверяем наличие текста
            if not message.text and not message.caption:
                logger.info("No text or caption in edited channel post, skipping")
                return
            
            text_to_check = message.text or message.caption or ""
            logger.info(f"Edited channel post text: {text_to_check[:100]}...")
            
            # Проверяем наличие ОБОИХ хэштегов: #новости И #upd
            text_lower = text_to_check.lower()
            has_news = "#новости" in text_lower
            has_upd = "#upd" in text_lower
            
            if not (has_news and has_upd):
                logger.info(f"Not both hashtags found (news: {has_news}, upd: {has_upd}), skipping")
                return
            
            logger.info(f"Edited news post with #upd detected from channel {NEWS_CHANNEL_ID}, starting broadcast")
            
            # Получаем всех пользователей из базы
            try:
                with db.get_cursor() as cursor:
                    cursor.execute("SELECT user_id FROM users")
                    users = cursor.fetchall()
                logger.info(f"Found {len(users)} users for broadcast")
            except Exception as e:
                logger.error(f"Failed to get users from database: {e}")
                return
            
            # Счётчики успешных/неудачных отправок
            success_count = 0
            fail_count = 0
            
            # Отправляем обновлённую новость всем пользователям
            for user in users:
                user_id = user[0]
                try:
                    await message.forward(user_id)
                    success_count += 1
                    await asyncio.sleep(0.05)  # Небольшая задержка между отправками
                except Exception as e:
                    fail_count += 1
                    logger.error(f"Failed to send updated news to user {user_id}: {e}")
            
            logger.info(f"Updated news broadcast completed: {success_count} success, {fail_count} failed")
            
            # Отправляем отчет админам
            report = (
                f"🔄 <b>Рассылка обновлённых новостей завершена</b>\n\n"
                f"✅ Успешно отправлено: {success_count}\n"
                f"❌ Не удалось отправить: {fail_count}\n"
                f"👥 Всего пользователей: {len(users)}\n\n"
                f"ℹ️ Отредактированный пост с #upd"
            )
            
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, report, parse_mode="HTML")
                    logger.info(f"Report sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send report to admin {admin_id}: {e}")
            
        except Exception as e:
            logger.error(f"Error in updated news broadcast: {e}")
    
    logger.info("All handlers registered")
