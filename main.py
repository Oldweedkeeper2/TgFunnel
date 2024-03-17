import asyncio

from app.main import app, send_messages_loop
from app.logger import logger

if __name__ == "__main__":
    try:
        logger.info("Starting bot...")
        app.loop.create_task(send_messages_loop())
        app.run()
        
        logger.info("Bot stopped.")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
