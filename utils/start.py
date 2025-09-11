import asyncio
import core.bot as bot
# import core.web as web
import core.records as records
import utils.setup_bot_test as setup

#If file is ran
if __name__ == "__main__":
    # asyncio.run(records.main())
    setup.main()
    bot.start()