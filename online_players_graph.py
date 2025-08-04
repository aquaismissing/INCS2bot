from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING

import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import ScalarMappable
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedFormatter
import pandas as pd
import seaborn as sns

import config
from functions import utime, caching
from functions.ulogging import get_logger

if TYPE_CHECKING:
    from typing import BinaryIO

MINUTE = 60
MAX_ONLINE_MARKS = (MINUTE // 10) * 24 * 7 * 2  # = 2016 marks - every 10 minutes for the last two weeks
ALLOWED_HOSTS = {'kappa.lol', 'gachi.gay', 'femboy.beauty', 'segs.lol'}  # https://github.com/0Supa/uploader

logger = get_logger('online_players_graph', config.LOGS_FOLDER, config.LOGS_CONFIG_FILE_PATH)

scheduler = BlockingScheduler()

cmap = LinearSegmentedColormap.from_list('custom', [(1, 1, 0), (1, 0, 0)], N=100)
norm = plt.Normalize(0, 2_000_000)
mappable = ScalarMappable(norm=norm, cmap=cmap)

ticks = [0, 250000, 500000, 750000, 1000000, 1250000, 1500000, 1750000, 2000000]
colorbar_ticks_format = FixedFormatter(['0', '250K', '500K', '750K', '1M', '1.25M', '1.5M', '1.75M', '2M+'])
fig_ticks_format = ['' for _ in ticks]

x_major_locator = mdates.DayLocator()
x_major_formatter = mdates.DateFormatter('%b %d')


def upload_image_online(image: BinaryIO, host: str) -> dict[str, ...]:
    if host not in ALLOWED_HOSTS:
        raise TypeError(f'unknown host, choose one of these: {ALLOWED_HOSTS}')

    response = requests.post(f'https://{host}/api/upload',
                             headers=config.REQUESTS_HEADERS,
                             files={'file': image})

    if response.status_code != 200:
        logger.error(f'Caught error while uploading graph image to the file uploader ({host})!',
                     response.status_code, response.reason, response.text)
        return {'link': ''}

    return response.json()


def delete_uploaded_image(host: str, image_key: str) -> bool:
    if host not in ALLOWED_HOSTS:
        raise TypeError(f'unknown host, choose one of these: {ALLOWED_HOSTS}')

    response = requests.post(f'https://{host}/api/delete',
                             headers=config.REQUESTS_HEADERS,
                             data={'key': image_key})

    if response.status_code != 200:
        logger.error(f'Caught error while uploading graph image to the file uploader ({host})!',
                     response.status_code, response.reason, response.text)
        return False

    return response.json().get('success', False)


def upload_image_to_catbox(image: BinaryIO) -> str:  # might be blocked on some hostings
    response = requests.post('https://catbox.moe/user/api.php',
                             headers=config.REQUESTS_HEADERS,
                             data={'reqtype': 'fileupload'},
                             files={'fileToUpload': image})

    if response.status_code != 200:
        logger.error('Caught error while uploading graph image to the file uploader (catbox.moe)!',
                     response.status_code, response.reason, response.text)
        return ''

    return response.text


@scheduler.scheduled_job('cron', hour='*', minute='0,10,20,30,40,50', second='0')
def graph_maker():
    # noinspection PyBroadException
    try:
        old_player_data = pd.read_csv(config.PLAYER_CHART_FILE_PATH, parse_dates=['DateTime'])

        marks_count = len(old_player_data.index)
        if marks_count >= MAX_ONLINE_MARKS:
            remove_marks = marks_count - MAX_ONLINE_MARKS
            old_player_data.drop(range(remove_marks + 1), axis=0, inplace=True)

        with open(config.GC_CACHE_FILE_PATH, encoding='utf-8') as f:
            player_count = json.load(f).get('online_players', 0)

        if player_count < 50_000:  # potentially Steam maintenance
            player_count = old_player_data.iloc[-1]['Players']

        temp_player_data = pd.DataFrame(
            [[f'{utime.utcnow():%Y-%m-%d %H:%M:%S}', player_count]],
            columns=['DateTime', 'Players'],
        )

        new_player_data = pd.concat([old_player_data, temp_player_data])

        new_player_data.to_csv(config.PLAYER_CHART_FILE_PATH, index=False)

        fig: plt.Figure
        ax: plt.Axes

        sns.set_style('whitegrid')

        fig, ax = plt.subplots(figsize=(10, 2.5))
        ax.scatter('DateTime', 'Players',
                   data=new_player_data,
                   c='Players', cmap=cmap, s=10, norm=norm, linewidths=0.7)
        ax.fill_between(new_player_data['DateTime'],
                        new_player_data['Players'] - 20_000,
                        color=cmap(0.5), alpha=0.4)
        ax.margins(x=0)

        ax.grid(visible=True, axis='y', linestyle='--', alpha=0.3)
        ax.grid(visible=False, axis='x')
        ax.spines['bottom'].set_position('zero')
        ax.spines['bottom'].set_color('black')
        ax.set(xlabel='', ylabel='')
        ax.xaxis.set_ticks_position('bottom')
        ax.xaxis.set_major_locator(x_major_locator)
        ax.xaxis.set_major_formatter(x_major_formatter)
        ax.legend(loc='upper left')
        ax.text(0.20, 0.88,
                'Made by @INCS2\n'
                'updates every 10 min',
                ha='center', transform=ax.transAxes, color='black', size='8')
        ax.set_yticks(ticks, fig_ticks_format)

        fig.colorbar(mappable, ax=ax,
                     ticks=ticks,
                     format=colorbar_ticks_format,
                     pad=0.01)

        fig.subplots_adjust(top=0.933, bottom=0.077, left=0.03, right=1.07)

        fig.savefig(config.GRAPH_IMG_FILE_PATH, dpi=200)
        plt.close()

        cache = caching.load_cache(config.GRAPH_CACHE_FILE_PATH)

        try:
            response = delete_uploaded_image('kappa.lol', cache['key'])
        except (requests.HTTPError, requests.ConnectionError):
            logger.exception('Caught exception while deleting old graph image from the file uploader!')
            response = False

        if not response:
            logger.error('Failed to delete old graph image from the file uploader!')

        try:
            with open(config.GRAPH_IMG_FILE_PATH, 'rb') as f:
                response = upload_image_online(f, 'kappa.lol')
        except (requests.HTTPError, requests.ConnectionError):
            logger.exception('Caught exception while uploading graph image to the file uploader!')
            response = {'link': '', 'key': ''}

        caching.dump_cache(config.GRAPH_CACHE_FILE_PATH, response)
        logger.info('Successfully plotted the player count graph.')
    except Exception:
        logger.exception('Caught exception in graph maker!')
        time.sleep(MINUTE)
        return graph_maker()


def main():
    try:
        scheduler.start()
        logger.info('Started.')
    except KeyboardInterrupt:
        logger.info('Terminated.')


if __name__ == '__main__':
    main()
