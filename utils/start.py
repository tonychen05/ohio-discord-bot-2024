import multiprocessing
import asyncio
import core.bot as bot
# import core.web as web
import core.records as records

#If file is ran
if __name__ == "__main__":

    #Initialize the database
    asyncio.run(records.main())

    #Start Multithreading process for web and the bot
    discord_process = multiprocessing.Process(target=bot.start)
    # web_process = multiprocessing.Process(target=web.start)

    #Start Respective Process
    discord_process.start()
    # web_process.start()