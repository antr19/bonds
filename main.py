import asyncio

from src.dispatcher.dispatcher import CronDispatcher
from src.parser.parser import parser
from src.collector.collector import collector
from src.config import config

async def main():
    dispatcher = CronDispatcher()

    for job in config["jobs"]:
        if job["app"] == "parser":
            dispatcher.add_job(parser, day_of_week=job.get('day_of_week'), hour=job['hour'], minute=job['minute'])
        elif job["app"] == "collector":
            dispatcher.add_job(collector, day_of_week=job.get('day_of_week'), hour=job['hour'], minute=job['minute'])

    await dispatcher.start()


if __name__ == "__main__":
    asyncio.run(main())