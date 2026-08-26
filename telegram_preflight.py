import asyncio
import os

from telegram import Bot


async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing.")

    bot = Bot(token)

    try:
        me = await bot.get_me()
        print(f"Bot: @{me.username}")
        print("Bot ID:", me.id)

        print()
        print("Bot configuration is valid.")
        print("To discover the channel ID, send a message in the")
        print("announcement channel after the bot is an administrator.")
    finally:
        await bot.shutdown()


asyncio.run(main())
