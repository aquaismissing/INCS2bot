from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Type

from pyrogram import Client
from pyrogram.enums import ChatAction, ChatType, ParseMode
from pyrogram.errors.exceptions.bad_request_400 import MessageIdInvalid
from pyrogram.types import (CallbackQuery, InlineQuery, Message,
                            MessageEntity, InlineKeyboardMarkup,
                            ReplyKeyboardMarkup,
                            ReplyKeyboardRemove, ForceReply, User)
# noinspection PyUnresolvedReferences
from pyropatch import pyropatch  # do not delete!!

from .extended_ik import ExtendedIKM
from .logger import BotLogger
from .menu import Menu, NavMenu, FuncMenu
from .sessions import UserSession, UserSessions
from .stats import BotRegularStats

__all__ = ('BotClient',)


logger = logging.getLogger('INCS2bot')


class BotClient(Client):
    """
    Custom pyrogram.Client class to add custom properties and methods and stop PyCharm annoy me.
    """

    MAINLOOP_TIMEOUT = dt.timedelta(seconds=10)  # define how often mainloop tasks are being handled

    WILDCARD = '_'

    def __init__(self, *args, telegram_logger: BotLogger,
                 navigate_back_callback: str, commands_prefix: str = '/', **kwargs):
        super().__init__(*args, **kwargs)

        self.telegram_logger = telegram_logger
        self.navigate_back_callback = navigate_back_callback

        self._sessions: UserSessions = UserSessions()

        self._commands: dict[str, tuple | dict] = {}
        self.commands_prefix = commands_prefix

        # menus
        self._menus: dict[str, Menu] = {}
        self._menu_routes: dict[str, Menu | dict[str, Menu]] = {}

        self.is_in_mainloop = False

        # injects
        self._func_at_exception: callable = None

        self.startup_dt = None

        self.rstats = BotRegularStats()

    @property
    def sessions(self) -> UserSessions:
        return self._sessions

    async def start(self):
        self.startup_dt = dt.datetime.now(dt.UTC)
        await super().start()

    async def mainloop(self):
        # ESSENTIALS FOR MAINLOOP
        import signal
        from signal import signal as signal_fn, SIGINT, SIGTERM, SIGABRT

        signals = {k: v for v, k in signal.__dict__.items()
                   if v.startswith('SIG') and not v.startswith('SIG_')}
        task = None

        def signal_handler(signum, __):
            logger.info(f'Stop signal received ({signals[signum]}). Exiting...')
            task.cancel()

        for s in (SIGINT, SIGTERM, SIGABRT):
            signal_fn(s, signal_handler)
        # ESSENTIALS FOR MAINLOOP END

        self.is_in_mainloop = True
        while self.is_in_mainloop:
            task = asyncio.create_task(asyncio.sleep(self.MAINLOOP_TIMEOUT.total_seconds()))
            try:
                await task
                await self.telegram_logger.process_queue()
            except asyncio.CancelledError:
                self.is_in_mainloop = False

    async def register_session(self, user: User, message: Message = None) -> UserSession:
        session = await self._sessions.register_session(user, message)
        self.rstats.unique_users_served.add(user.id)
        return session

    async def dump_sessions(self):
        await self.clear_timeout_sessions()
        await self._sessions.sync_with_db()

    async def clear_timeout_sessions(self):
        """Clear all sessions that exceed a given lifetime."""

        return await self._sessions.clear_timeout_sessions()

    def clear_sessions(self):
        self._sessions.clear()

    def on_callback_exception(self):
        def decorator(func):
            async def inner(client: BotClient, session: UserSession, bot_message: Message, exc: Exception,
                            *args, **kwargs):
                message = await func(client, session, bot_message, exc, *args, **kwargs)
                if isinstance(message, Message):
                    session.last_bot_pm_id = message.id

            self._func_at_exception = inner
            return inner

        return decorator

    def on_command(self, command: str, *args, **kwargs):
        def decorator(func):
            self._commands[self.commands_prefix + command] = (func, args, kwargs)
            return func

        return decorator

    def _menu_factory(self,
                      _type: Type[Menu],
                      query: str,
                      *args,
                      _id: str,
                      came_from: Menu,  # menu where we clicked on button
                      ignore_message_not_modified: bool,
                      **kwargs):
        def decorator(func: callable | Menu):
            nonlocal _id

            if isinstance(func, Menu):
                menu = _type(func.id, func.func, *args,
                             came_from_menu_id=func.came_from_menu_id,
                             ignore_message_not_modified=func.ignore_message_not_modified,
                             **kwargs)
            else:
                if _id is None:
                    _id = func.__qualname__

                menu = _type(_id, func, *args, ignore_message_not_modified=ignore_message_not_modified, **kwargs)
                if came_from is not None:
                    menu.came_from_menu_id = came_from.id

            if menu not in self._menus.values():
                self.register_menu(menu)

            if came_from is None:
                self._menu_routes[query] = menu
                return menu

            if self._menu_routes.get(query):
                self._menu_routes[query][came_from.id] = menu
            else:
                self._menu_routes[query] = {came_from.id: menu}
            return menu

        return decorator

    def navmenu(self,
                query: str,
                *args,
                _id: str = None,
                came_from: callable | Menu = None,
                ignore_message_not_modified: bool = False,
                **kwargs):
        return self._menu_factory(NavMenu,
                                  query,
                                  *args,
                                  _id=_id,
                                  came_from=came_from,
                                  ignore_message_not_modified=ignore_message_not_modified,
                                  **kwargs)

    def funcmenu(self,
                 query: str,
                 *args,
                 _id: str = None,
                 came_from: callable | Menu = None,
                 ignore_message_not_modified: bool = False,
                 **kwargs):
        return self._menu_factory(FuncMenu,
                                  query,
                                  *args,
                                  _id=_id,
                                  came_from=came_from,
                                  ignore_message_not_modified=ignore_message_not_modified,
                                  **kwargs)

    @staticmethod
    def callback_process(of: callable | NavMenu):
        def decorator(func: callable):
            if not isinstance(of, NavMenu):
                raise TypeError('process can be set only to navmenu u doofus')

            async def inner(client: BotClient, session: UserSession, query: CallbackQuery,
                            *args, **kwargs):
                message = await func(client, session, query, *args, **kwargs)
                if isinstance(message, Message):
                    session.last_bot_pm_id = message.id

            of.callback_process = inner
            return inner

        return decorator

    @staticmethod
    def message_process(of: callable | NavMenu):
        def decorator(func: callable):
            if not isinstance(of, NavMenu):
                raise TypeError('process can be set only to navmenu u doofus')

            async def inner(client: BotClient, session: UserSession, bot_message: Message, user_input: Message,
                            *args, **kwargs):
                await client.log_message(session, user_input)
                if bot_message.chat is None:  # if user blocked the bot and deleted the message history before
                    bot_message = await client.send_message(user_input.chat.id, ".")
                    message = await client._func_at_exception(client, session, bot_message, None)
                else:
                    try:
                        message = await func(client, session, bot_message, user_input, *args, **kwargs)
                    except MessageIdInvalid:  # if user deleted bot_message for some reason
                        message = await client.send_message(user_input.chat.id, ".")
                if isinstance(message, Message):
                    bot_message = message
                    session.last_bot_pm_id = bot_message.id
                return await client.go_back(session, bot_message)

            of.message_process = inner
            return inner

        return decorator

    async def handle_message(self, message: Message):
        if message.text is None:
            return

        user = message.from_user

        if message.chat.type != ChatType.PRIVATE:
            text = message.text
            if text.startswith(self.commands_prefix) and self.has_a_command(text):
                session = await self.register_session(user, message)  # early command handling in group chats
                return await self.handle_command(session, message)    # of every single user of these
            return

        session = await self.register_session(user, message)

        current_menu = self.get_menu_by_id(session.current_menu_id)
        if isinstance(current_menu, NavMenu) and current_menu.has_message_process():
            if session.last_bot_pm_id is None:  # handling message processes after reload
                menu = self.get_wildcard_menu()
                return await self.jump_to_menu(session, message, menu)
            bot_message = await self.get_messages(message.chat.id, session.last_bot_pm_id)
            return await current_menu.message_process(self, session, bot_message, message)

        await self.log_message(session, message)

        if message.text.startswith(self.commands_prefix):
            return await self.handle_command(session, message)

    async def handle_command(self, session: UserSession, message: Message):
        prompt = message.text

        if not self.has_a_command(prompt):
            return
        if '@' in prompt:
            prompt, username = prompt.split('@', 2)
            username, *commands_args = username.split()
            if username != self.me.username:
                return

        prompt = prompt.split()[0]

        func, args, kwargs = self.get_func_by_command(prompt)
        await message.reply_chat_action(ChatAction.TYPING)
        return await func(self, session, message, *args, **kwargs)

    def has_a_command(self, prompt: str):
        if '@' in prompt:
            prompt, _ = prompt.split('@', 2)

        return prompt.split()[0] in self._commands

    async def handle_callback(self, callback_query: CallbackQuery):
        if callback_query.message.chat.type != ChatType.PRIVATE:
            return

        user = callback_query.from_user
        session = self.sessions.get(user.id)
        if session is None:
            session = await self.register_session(user, callback_query.message)

        if callback_query.message.chat.id != self.telegram_logger.log_channel_id:
            await self.log_callback(session, callback_query)

        bot_message = callback_query.message
        if callback_query.data == self.navigate_back_callback:
            return await self.go_back(session, bot_message)

        return await self.get_menu_by_callback(session, callback_query)

    def get_wildcard_command(self):
        return self._commands.get(self.WILDCARD)

    def get_func_by_command(self, prompt: str):
        return self._commands.get(prompt)

    async def get_menu_by_callback(self, session: UserSession, callback_query: CallbackQuery):
        is_going_to_wildcard_menu = False
        wildcard_menu = self.get_wildcard_menu()

        menu = self.get_menu_by_query(session.current_menu_id, callback_query.data)
        if menu is None:
            if wildcard_menu is None:
                return

            current_menu = self.get_menu_by_id(session.current_menu_id)
            if current_menu is None:                        # happens if the user clicks on the menu
                session.current_menu_id = wildcard_menu.id  # but there is no user data
                return await self.get_menu_by_callback(session, callback_query)

            if isinstance(current_menu, NavMenu) and current_menu.has_callback_process():
                try:
                    return await current_menu.callback_process(self, session, callback_query)
                except asyncio.exceptions.TimeoutError:
                    return

            is_going_to_wildcard_menu = True

        self.rstats.callback_queries_handled += 1

        bot_message = callback_query.message
        try:
            if is_going_to_wildcard_menu:
                return await self.jump_to_menu(session, bot_message, wildcard_menu)
            await self.go_to_menu(session, bot_message, menu)
        except Exception as e:
            self.rstats.exceptions_caught += 1
            await self._func_at_exception(self, session, bot_message, e)

    def register_menu(self, menu: Menu):
        if menu not in self._menus.values():
            self._menus[menu.id] = menu

    def get_menu_by_id(self, _id: str):
        return self._menus.get(_id)

    def get_menus_by_query(self, query: str):
        return self._menu_routes.get(query)

    def get_menu_by_query(self, current_menu_id: str, query: str):
        possible_menus = self.get_menus_by_query(query)
        if isinstance(possible_menus, Menu):
            return possible_menus

        return possible_menus[current_menu_id]

    def get_wildcard_menu(self):
        return self._menu_routes.get(self.WILDCARD)

    async def go_to_menu(self, session: UserSession, bot_message: Message, menu: Menu):
        """
        Sends user to a specific menu if we can access that menu from the current one.

        Note:
            You can use ``BotClient.jump_to_menu(session, callback_query, menu)`` to avoid access check.
        """

        if not menu.can_come_from(session.current_menu_id):
            raise AttributeError(f"Can't access {menu} from {self.get_menu_by_id(session.current_menu_id)}")

        return await self.jump_to_menu(session, bot_message, menu)

    async def jump_to_menu(self, session: UserSession, bot_message: Message, menu: Menu):
        """Sends user to a specific menu."""

        if isinstance(menu, NavMenu):
            session.previous_menu_id = menu.came_from_menu_id
            session.current_menu_id = menu.id

        result = await menu(self, session, bot_message)
        if isinstance(result, Message):
            session.last_bot_pm_id = result.id
        return result

    async def jump_to_wildcard_menu(self, session: UserSession, bot_message: Message):
        menu = self.get_wildcard_menu()
        if menu is None:
            return
        return await menu(self, session, bot_message)

    async def go_back(self, session: UserSession, bot_message: Message):
        previous_menu = self.get_menu_by_id(session.previous_menu_id)
        if previous_menu is None:
            previous_menu = self.get_wildcard_menu()
            if previous_menu is None:
                return

        return await self.jump_to_menu(session, bot_message, previous_menu)

    # noinspection PyUnresolvedReferences
    async def listen_message(self,
                             chat_id: int,
                             filters=None,
                             timeout: int = None) -> Message:
        return await super().listen_message(chat_id, filters, timeout)

    # noinspection PyUnresolvedReferences
    async def ask_message(self,
                          chat_id: int,
                          text: str,
                          filters=None,
                          timeout: int = None,
                          parse_mode: ParseMode = None,
                          entities: list[MessageEntity] = None,
                          disable_web_page_preview: bool = None,
                          disable_notification: bool = None,
                          reply_to_message_id: int = None,
                          schedule_date: dt.datetime = None,
                          protect_content: bool = None,
                          reply_markup: InlineKeyboardMarkup | ReplyKeyboardMarkup |
                          ReplyKeyboardRemove | ForceReply = None) -> Message:
        return await super().ask_message(chat_id,
                                         text,
                                         filters,
                                         timeout,
                                         parse_mode,
                                         entities,
                                         disable_web_page_preview,
                                         disable_notification,
                                         reply_to_message_id,
                                         schedule_date,
                                         protect_content,
                                         reply_markup)

    # noinspection PyUnresolvedReferences
    async def listen_callback(self,
                              chat_id: int = None,
                              message_id: int = None,
                              inline_message_id: str = None,
                              filters=None,
                              timeout: int = None) -> CallbackQuery:
        return await super().listen_callback(chat_id,
                                             message_id,
                                             inline_message_id,
                                             filters,
                                             timeout)

    async def ask_message_silently(self, message: Message,
                                   text: str, *args,
                                   reply_markup: ExtendedIKM = None, timeout: int = None, **kwargs) -> Message:
        """Asks for a message in the same message."""

        await message.edit(text, *args, reply_markup=reply_markup, **kwargs)
        return await self.listen_message(message.chat.id, timeout=timeout)

    async def ask_callback_silently(self, message: Message,
                                    text: str, *args,
                                    reply_markup: ExtendedIKM = None, timeout: int = None, **kwargs) -> CallbackQuery:
        """Asks for a callback query in the same message."""

        await message.edit(text, *args, reply_markup=reply_markup, **kwargs)
        return await self.listen_callback(message.chat.id, message.id, timeout=timeout)

    async def log(self, text: str, *, disable_notification: bool = True,
                  reply_markup: ReplyKeyboardMarkup = None, parse_mode: ParseMode = None, instant: bool = False):
        """Sends log to the log channel."""

        if instant:  # made for specific log messages (e.g. "Bot is shutting down...")
            await self.telegram_logger.send_log(self, text, disable_notification, reply_markup, parse_mode)
            return

        await self.telegram_logger.schedule_system_log(self, text, disable_notification, reply_markup, parse_mode)

    async def log_message(self, session: UserSession, message: Message):
        """Sends message log to the log channel."""

        if self.test_mode:
            return

        await self.telegram_logger.schedule_message_log(self, session, message)

    async def log_callback(self, session: UserSession, callback_query: CallbackQuery):
        """Sends callback query log to the log channel."""

        if self.test_mode:
            return

        await self.telegram_logger.schedule_callback_log(self, session, callback_query)

    async def log_inline(self, session: UserSession, inline_query: InlineQuery):
        """Sends an inline query log to the log channel."""

        if self.test_mode:
            return

        await self.telegram_logger.schedule_inline_log(self, session, inline_query)
