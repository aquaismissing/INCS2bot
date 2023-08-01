from pyrogram import filters

from utypes import GunInfo


def callback_data_equals(data):
    async def func(flt, _, query):
        return flt.data == query.data

    return filters.create(func, data=data)


async def _callback_data_is_gun_func(_, __, query):
    return True if GunInfo.load().get(query.data) else False


callback_data_is_gun_filter = filters.create(_callback_data_is_gun_func)
