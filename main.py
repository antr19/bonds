import asyncio
import yaml

from src.dispatcher.dispatcher import CronDispatcher
from src.parser.parser import parser
from src.collector.collector import collector

async def main():
    dispatcher = CronDispatcher()

    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    for job in config["jobs"]:
        if job["app"] == "parser":
            dispatcher.add_job(parser, day_of_week=job.get('day_of_week'), hour=job['hour'], minute=job['minute'])
        elif job["app"] == "collector":
            dispatcher.add_job(collector, day_of_week=job.get('day_of_week'), hour=job['hour'], minute=job['minute'])

    await dispatcher.start()


if __name__ == "__main__":
    asyncio.run(main())