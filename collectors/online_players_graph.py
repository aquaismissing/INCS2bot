import datetime as dt
import json
import logging
import time

from apscheduler.schedulers.blocking import BlockingScheduler
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from requests import JSONDecodeError
import seaborn as sns
from telegraph import Telegraph

# noinspection PyUnresolvedReferences
import env
import config
from functions import utime

MINUTE = 60
MAX_ONLINE_MARKS = (MINUTE // 10) * 24 * 7 * 2  # = 2016 marks - every 10 minutes for the last two weeks

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

scheduler = BlockingScheduler()
telegraph = Telegraph(access_token=config.TELEGRAPH_ACCESS_TOKEN)


@scheduler.scheduled_job('cron', hour='*', minute='0,10,20,30,40,50', second='0')
def graph_maker():
    # noinspection PyBroadException
    try:
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        old_player_data = pd.read_csv(config.PLAYER_CHART_FILE_PATH, parse_dates=['DateTime'])

        marks_count = len(old_player_data.index)
        if marks_count >= MAX_ONLINE_MARKS:
            remove_marks = marks_count - MAX_ONLINE_MARKS
            old_player_data.drop(range(remove_marks + 1), axis=0, inplace=True)

        player_count = cache.get('online_players', 0)
        if player_count < 50_000:  # potentially Steam maintenance
            player_count = old_player_data.iloc[-1]['Players']

        temp_player_data = pd.DataFrame(
            [[f'{utime.utcnow():%Y-%m-%d %H:%M:%S}', player_count]],
            columns=["DateTime", "Players"],
        )

        new_player_data = pd.concat([old_player_data, temp_player_data])

        new_player_data.to_csv(config.PLAYER_CHART_FILE_PATH, index=False)

        sns.set_style('whitegrid')

        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.plot('DateTime', 'Players',
                data=new_player_data,
                color='red', linewidth=0.7, marker='o', markevery=[-1])
        ax.fill_between(new_player_data['DateTime'],
                        new_player_data['Players'],
                        0,
                        facecolor='red', color='red', alpha=0.4)

        ax.margins(x=0)
        ax.grid(visible=True, axis="y", linestyle="--", alpha=0.3)
        ax.grid(visible=False, axis="x")
        ax.spines["bottom"].set_position("zero")
        ax.spines["bottom"].set_color("black")
        ax.set_ylabel("")
        ax.set_xlabel("")
        ax.xaxis.set_ticks_position("bottom")
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.legend(loc="upper left")
        ax.axhline(y=0, color="none")
        ax.axhline(y=1400000, color="none")

        plt.yticks(ticks=[0, 250000, 500000, 750000, 1000000, 1250000])
        plt.subplots_adjust(top=1, bottom=0.077, left=0, right=1)
        plt.text(0.989, 0.058, "0", transform=ax.transAxes, alpha=0.3)
        plt.text(0.965, 0.215, "250k", transform=ax.transAxes, alpha=0.3)
        plt.text(0.965, 0.377, "500k", transform=ax.transAxes, alpha=0.3)
        plt.text(0.965, 0.54, "700k", transform=ax.transAxes, alpha=0.3)
        plt.text(0.951, 0.705, "1 000k", transform=ax.transAxes, alpha=0.3)
        plt.text(0.951, 0.865, "1 250k", transform=ax.transAxes, alpha=0.3)
        plt.text(0.156, 0.874, "Made by @INCS2\nupd every 10 min",
                 ha="center", transform=ax.transAxes, color="black",
                 size="6")
        plt.close()

        fig.savefig(config.GRAPH_IMG_FILE_PATH)
        try:
            image_path = telegraph.upload_file(str(config.GRAPH_IMG_FILE_PATH))[0]['src']
        except JSONDecodeError:  # SCREW YOU
            time.sleep(1)
            image_path = telegraph.upload_file(str(config.GRAPH_IMG_FILE_PATH))[0]['src']
        image_url = f'https://telegra.ph{image_path}'

        if image_url != cache.get('graph_url'):
            cache['graph_url'] = image_url

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception:
        logging.exception('Caught exception in graph maker!')
        time.sleep(MINUTE)
        return graph_maker()


def main():
    scheduler.start()


if __name__ == "__main__":
    main()
