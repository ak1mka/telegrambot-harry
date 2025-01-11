import telebot
import random
import time
import sqlite3
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


token = '7519810304:AAE54qNpBJPt-nex_gepDUgMueakxwvxifg'
channel_username = '@harrytokensol'

bot = telebot.TeleBot(token)


conn = sqlite3.connect('user_data.db', check_same_thread=False)
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    solana_address TEXT,
    points INTEGER DEFAULT 0,
    last_collect INTEGER DEFAULT 0
)
''')
conn.commit()


def is_subscribed(user_id):
    try:
        status = bot.get_chat_member(channel_username, user_id).status
        return status in ['member', 'administrator', 'creator']
    except Exception:
        return False


def register_solana_address(user_id, solana_address):
    cursor.execute('INSERT OR IGNORE INTO users (user_id, solana_address) VALUES (?, ?)', (user_id, solana_address))
    conn.commit()


def update_points(user_id, points):
    cursor.execute('UPDATE users SET points = points + ?, last_collect = ? WHERE user_id = ?', (points, int(time.time()), user_id))
    conn.commit()

def get_user_data(user_id):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    return cursor.fetchone()


main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_keyboard.add(KeyboardButton("Мой профиль👤"))
main_keyboard.add(KeyboardButton("Claim✅"))
main_keyboard.add(KeyboardButton("Leaderboard🏆"))


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if not is_subscribed(user_id):
        bot.reply_to(message, f"Please write to our channel {channel_username} to use the bot.")
        return

    user_data = get_user_data(user_id)
    if user_data:
        bot.reply_to(message, "You are already registered! Use the buttons below to interact with the bot.", reply_markup=main_keyboard)
    else:
        bot.reply_to(message, "Hello! Please send your Solana address for registration.", reply_markup=main_keyboard)
        bot.register_next_step_handler(message, process_solana_address)


def process_solana_address(message):
    user_id = message.from_user.id
    solana_address = message.text.strip()

    if len(solana_address) < 32 or len(solana_address) > 44:  
        bot.reply_to(message, "Please enter a valid Solana address.")
        bot.register_next_step_handler(message, process_solana_address)
        return

    register_solana_address(user_id, solana_address)
    bot.reply_to(message, "Your Solana address has been successfully registered! You can now use the buttons below.", reply_markup=main_keyboard)


@bot.message_handler(func=lambda message: message.text == "My profile👤")
def my_profile(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    if not user_data:
        bot.reply_to(message, "You are not registered yet. Use /start to get started.")
        return

    solana_address = user_data[1]
    points = user_data[2]
    bot.reply_to(message, f"Your profile:\nSolana address: {solana_address}\nAccumulated Harry points: {points}")


@bot.message_handler(func=lambda message: message.text == "Claim✅")
def collect_points(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)

    if not user_data:
        bot.reply_to(message, "You haven't registered yet. Use /start to start.")
        return

    last_collect = user_data[3]
    if time.time() - last_collect < 3600:
        remaining_time = int(3600 - (time.time() - last_collect))
        bot.reply_to(message, f"You have already collected points. Try again in {remaining_time // 60} minutes and {remaining_time % 60} seconds.")
        return

    points = random.randint(60, 100)
    update_points(user_id, points)
    bot.reply_to(message, f"You collected {points} Harry points! Your total account: {user_data[2] + points} Harry points")

@bot.message_handler(func=lambda message: message.text == "Leaderboard🏆")
def leaderboard(message):
    cursor.execute('SELECT user_id, points FROM users ORDER BY points DESC LIMIT 10')
    top_users = cursor.fetchall()

    leaderboard_text = "🏆 Leaderboard:\n"
    for i, (user_id, points) in enumerate(top_users, start=1):
        leaderboard_text += f"{i}. User {user_id}: {points} Harry points\n"

    bot.reply_to(message, leaderboard_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.reply_to(message, "Here is a list of available commands:\n/start - begin\n/help - help\nYou can also use the buttons on your keyboard.")

if __name__ == "__main__":
    print("Бот запущен и работает...")
    bot.infinity_polling()

