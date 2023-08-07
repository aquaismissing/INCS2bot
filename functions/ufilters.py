from pyrogram import filters

from utypes import GunInfo

callback_queries_available = set()  # todo: redo or delete


def callback_data_equals(data):
    async def func(flt, _, query):
        return flt.data == query.data

    callback_queries_available.add(data)
    return filters.create(func, data=data)


async def _any_callback_query_available_func(_, __, query):
    return True if query.data in callback_queries_available else False


any_callback_query_available = filters.create(_any_callback_query_available_func)


async def _callback_data_is_gun_func(_, __, query):
    return True if GunInfo.load().get(query.data) else False


callback_data_is_gun_filter = filters.create(_callback_data_is_gun_func)
