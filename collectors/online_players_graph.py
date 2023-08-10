import datetime as dt
import json
import logging
import time

from apscheduler.schedulers.blocking import BlockingScheduler
from html_telegraph_poster.upload_images import upload_image
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# noinspection PyUnresolvedReferences
import env
import config

MINUTE = 60

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")

scheduler = BlockingScheduler()


@scheduler.scheduled_job('cron', hour='*', minute='0,10,20,30,40,50', second='0')
def graph_maker():
    try:
        with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
            cache = json.load(f)

        player_count = cache.get('online_players', 0)

        old_player_data = pd.read_csv(config.PLAYER_CHART_FILE_PATH,
                                      parse_dates=['DateTime'])

        if len(old_player_data.index) >= 10:
            old_player_data.drop(0, axis=0, inplace=True)

        temp_player_data = pd.DataFrame(
            [[f'{dt.datetime.utcnow():%Y-%m-%d %H:%M:%S}', player_count]],
            columns=["DateTime", "Players"],
        )
        temp_player_data["Players"] = temp_player_data["Players"].astype("int64")

        new_player_data = pd.concat([old_player_data, temp_player_data])

        new_player_data.to_csv(config.PLAYER_CHART_FILE_PATH, index=False)

        sns.set_style("whitegrid")

        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.plot(
            "DateTime",
            "Players",
            data=new_player_data,
            color="red",
            linewidth=0.7,
            marker="o",
            markevery=[-1],
        )
        ax.fill_between(
            new_player_data["DateTime"],
            new_player_data["Players"],
            0,
            facecolor="red",
            color="red",
            alpha=0.4,
        )

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
        url = upload_image(str(config.GRAPH_IMG_FILE_PATH))

        if url != cache.get("graph_url"):
            cache['graph_url'] = url

        with open(config.CACHE_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=4)
    except Exception:
        logging.exception(f"Caught exception in graph maker!")
        time.sleep(MINUTE)
        return graph_maker()


def main():
    scheduler.start()


if __name__ == "__main__":
    main()
