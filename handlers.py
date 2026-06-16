"""
Обработчики команд и сообщений бота
Вынесены отдельно для чистоты кода
"""
import time
import logging
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config_serverless import ADMIN_CHAT_ID, REFERRAL_REWARD

logger = logging.getLogger(__name__)

# Анти-спам
user_last_action = defaultdict(float)
SPAM_COOLDOWN = 1


# FSM состояния
class Form(StatesGroup):
    waiting_for_promocode = State()


def get_main_keyboard():
    """Главная клавиатура"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⭐ Заработать звёзды")],
            [KeyboardButton(text="💰 Вывести звёзды")],
            [KeyboardButton(text="👤 Мой профиль")],
            [KeyboardButton(text="🎁 Промокод")]
        ],
        resize_keyboard=True
    )
    return keyboard


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
        
        if not user_exists:
            db.add_user(user_id, username, full_name, referrer_id)
            
            if referrer_id and referrer_id != user_id:
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
                                    f"🎉 По вашей ссылке зарегистрировался новый друг!\n"
                                    f"Вам начислено +{REFERRAL_REWARD} ⭐\n\n"
                                    f"👤 Новый реферал: {full_name}"
                                )
                                logger.info(f"Notification sent to referrer {referrer_id}")
                            except Exception as e:
                                logger.error(f"Failed to notify referrer {referrer_id}: {e}")
                    except Exception as e:
                        logger.error(f"Error checking referrer {referrer_id}: {e}")
        
        await message.answer(
            f"✨ Добро пожаловать, {full_name}!\n\n"
            "🌟 Реферальный бот для заработка Звёзд!\n\n"
            f"Приглашай друзей по своей реферальной ссылке и получай +{REFERRAL_REWARD} ⭐ за каждого!",
            reply_markup=get_main_keyboard()
        )
    
    
    @dp.message(F.text.in_(["⭐ Заработать звёзды", "💰 Вывести звёзды", "👤 Мой профиль", "🎁 Промокод"]))
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
            db.create_withdrawal(user_id, amount)
            
            username = callback.from_user.username or "Без username"
            full_name = callback.from_user.full_name
            admin_message = (
                f"📤 <b>Новая заявка на вывод</b>\n\n"
                f"👤 Имя: {full_name}\n"
                f"👤 Username: @{username}\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"💰 Сумма: {amount} ⭐\n"
                f"📊 Рефералов: {user_data['referral_count']}\n"
            )
            
            if amount == 350:
                admin_message += f"\n🎁 <b>TELEGRAM PREMIUM</b>"
            
            try:
                await bot.send_message(ADMIN_CHAT_ID, admin_message, parse_mode="HTML")
                logger.info(f"Withdrawal request sent to admin")
            except Exception as e:
                logger.error(f"Error sending withdrawal to admin: {e}")
            
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
        await callback.message.delete()
        await callback.message.answer(
            "✨ Главное меню",
            reply_markup=get_main_keyboard()
        )
    
    
    # Админ команды
    @dp.message(Command("create_promo"))
    async def create_promocode_command(message: types.Message):
        """Создание промокода"""
        if message.from_user.id != ADMIN_CHAT_ID:
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
        if message.from_user.id != ADMIN_CHAT_ID:
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
        if message.from_user.id != ADMIN_CHAT_ID:
            return
        
        try:
            stats = db.get_statistics()
            await message.answer(
                f"📊 <b>Статистика бота</b>\n\n"
                f"👥 Всего пользователей: {stats['total_users']}\n"
                f"💰 Всего звёзд в обороте: {stats['total_balance']} ⭐\n"
                f"🔗 Всего рефералов: {stats['total_referrals']}\n"
                f"📤 Всего выводов: {stats['total_withdrawals']}\n"
                f"💸 Сумма выводов: {stats['total_withdrawn']} ⭐",
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
    
    
    @dp.message(Command("set_balance"))
    async def set_balance_command(message: types.Message):
        """Установить баланс"""
        if message.from_user.id != ADMIN_CHAT_ID:
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
        if message.from_user.id != ADMIN_CHAT_ID:
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
    
    logger.info("All handlers registered")
