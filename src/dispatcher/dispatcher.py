import asyncio
from datetime import datetime
from typing import Callable, Optional


class CronDispatcher:
    def __init__(self):
        self.jobs = []
        self._last_check = None

    def add_job(self, coro_func: Callable, *args,
                day_of_week: Optional[int] = None,
                day: Optional[int] = None,
                hour: int = 0, minute: int = 0):
        """
        Добавляет задачу в расписание.

        day_of_week: 0=Пн, 6=Вс (используется для еженедельных задач)
        day: 1-31 (используется для ежемесячных задач)
        hour, minute: время запуска
        """
        self.jobs.append({
            'func': coro_func,
            'args': args,
            'day_of_week': day_of_week,
            'day': day,
            'hour': hour,
            'minute': minute
        })
        print("Добавлена новая задача:", coro_func.__name__)
        print("День недели:", day_of_week, "День:", day, "Час:", hour, "Минуты:", minute)

    def _should_run(self, job: dict, now: datetime) -> bool:
        """Проверяет, нужно ли запускать задачу сейчас."""
        if now.hour != job['hour'] or now.minute != job['minute']:
            return False

        if job['day_of_week'] is not None:
            return now.weekday() == job['day_of_week']

        if job['day'] is not None:
            return now.day == job['day']

        return True

    async def start(self):
        """Запускает диспетчер."""
        print("Cron диспетчер запущен")

        while True:
            now = datetime.now()

            # Проверяем задачи только при смене минуты
            if self._last_check is None or (
                    now.year != self._last_check.year or
                    now.month != self._last_check.month or
                    now.day != self._last_check.day or
                    now.hour != self._last_check.hour or
                    now.minute != self._last_check.minute
            ):
                for job in self.jobs:
                    if self._should_run(job, now):
                        asyncio.create_task(self._run_job(job))

                self._last_check = now

            await asyncio.sleep(1)

    async def _run_job(self, job: dict):
        """Запускает задачу с обработкой ошибок."""
        # try:
        await job['func'](*job['args'])
        # except Exception as e:
        #     print(f"Ошибка в задаче: {e}")
