# import env

import logging
import time
import json
import datetime as dt

import config
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from html_telegraph_poster.upload_images import upload_image

MINUTE = 60

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s | %(name)s: %(message)s",
                    datefmt="%H:%M:%S — %d/%m/%Y")


def graph_maker():
    with open(config.CACHE_FILE_PATH, encoding='utf-8') as f:
        cache = json.load(f)

    player_count = cache.get('online_players', 0)

    old_player_data = pd.read_csv(config.PLAYER_CHART_FILE_PATH,
                                  parse_dates=['DateTime'])

    if len(old_player_data.index) > 10:
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
        json.dump(cache, f)

    time.sleep(8 * MINUTE)


def main():
    while True:
        minutes = dt.datetime.now().minute
        if minutes % 10 == 0:
            try:
                return graph_maker()
            except Exception:
                logging.exception(f"Caught exception in graph maker!")
                time.sleep(2 * MINUTE)
        
        # sleep to closest (minute % 10 == 0) time
        seconds = dt.datetime.now().second
        microseconds = dt.datetime.now().microsecond
        snooze = ((10 - minutes % 10) * MINUTE) - (seconds + microseconds / 1000000.0)
        time.sleep(snooze)


if __name__ == "__main__":
    main()
