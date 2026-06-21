from __future__ import annotations
from apscheduler.schedulers.blocking import BlockingScheduler
from pipeline.scheduler.jobs import collect_and_analyze


def main():
    scheduler = BlockingScheduler(timezone="Asia/Jakarta")
    scheduler.add_job(collect_and_analyze, "cron", hour="8,18", minute=0)
    scheduler.start()


if __name__ == "__main__":
    main()
