from telethon import TelegramClient, events
import time
import logging
from collections import defaultdict

API_ID = ''
API_HASH = ''
PHONE_NUMBER = '+'
TARGET_CHAT = '' # @username
FLOOD_TIME = 10
MAX_MESSAGES = 3
MUTE_TIME = '5h'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

message_counts = defaultdict(list)
muted_users = {}

client = TelegramClient('userbot_session', API_ID, API_HASH)

def is_user_admin(user_id: int) -> bool:
    user_permissions = client.get_permissions(TARGET_CHAT, user_id)
    return user_permissions.is_admin

def clear_old_messages(user_id: int, current_time: float) -> None:
    message_counts[user_id] = [
        timestamp for timestamp in message_counts[user_id] if current_time - timestamp <= FLOOD_TIME
    ]

async def mute_user(username: str) -> None:
    command = f'/mute @{username} {MUTE_TIME} 18+ anti flood'
    await client.send_message(TARGET_CHAT, command)
    logger.info(f'Команда /mute отправлена для пользователя @{username}')

async def send_admin_message(username: str) -> None:
    command = 'Это администратор!'
    await client.send_message(TARGET_CHAT, command)
    logger.info(f'Отправлено сообщение для администратора @{username}')

async def handle_flood(event: events.NewMessage.Event) -> None:
    user_id = event.sender_id
    user = await event.get_sender()
    username = user.username if user.username else str(user_id)
    current_time = time.time()

    if user_id not in message_counts:
        message_counts[user_id] = []

    clear_old_messages(user_id, current_time)

    message_counts[user_id].append(current_time)

    if len(message_counts[user_id]) > MAX_MESSAGES:
        if is_user_admin(user_id):
            await send_admin_message(username)
        else:
            if user_id not in muted_users or current_time - muted_users[user_id] > 60:
                await mute_user(username)
                muted_users[user_id] = current_time
            else:
                logger.info(f'Для пользователя @{username} команда мута уже отправлена недавно.')

@client.on(events.NewMessage(chats=TARGET_CHAT))
async def anti_flood(event: events.NewMessage.Event):
    try:
        await handle_flood(event)
    except Exception as e:
        logger.error(f'Ошибка при обработке сообщения: {e}')

async def main():
    try:
        await client.start(PHONE_NUMBER)
        logger.info("Система антифлуда активирована.")
        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f'Произошла ошибка при запуске клиента: {e}')

if __name__ == '__main__':
    client.loop.run_until_complete(main())
