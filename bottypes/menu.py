from __future__ import annotations

import asyncio
import typing
from typing import Callable, TypeAlias

from pyrogram.errors import UserIsBlocked, MessageNotModified

if typing.TYPE_CHECKING:
    from .botclient import BotClient
    from .sessions import UserSession

    from pyrogram.types import CallbackQuery, Message

    MessageProcess: TypeAlias = Callable[[BotClient, UserSession, Message, Message], ...]
    CallbackProcess: TypeAlias = Callable[[BotClient, UserSession, CallbackQuery], ...]


class Menu:
    def __init__(self,
                 _id: str,
                 func: callable,
                 *args,
                 came_from_menu_id: str | None = None,
                 ignore_message_not_modified: bool,
                 **kwargs):
        self.id = _id

        # menu functionality
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.came_from_menu_id = came_from_menu_id

        # utils
        self.ignore_message_not_modified = ignore_message_not_modified

    async def __call__(self, client: BotClient, session: UserSession, bot_message: Message, *args, **kwargs):
        try:
            return await self.func(client, session, bot_message, *args, *self.args, **kwargs, **self.kwargs)
        except MessageNotModified:
            if not self.ignore_message_not_modified:
                raise
            return
        except UserIsBlocked:
            return
        except asyncio.exceptions.TimeoutError:
            return

    def __repr__(self):
        return f'<{self.__class__.__name__}(id={self.id}, func={self.func})>'

    def can_come_from(self, _id):
        return self.came_from_menu_id == _id


class NavMenu(Menu):
    def __init__(self,
                 _id: str,
                 func: callable,
                 *args,
                 came_from_menu_id: str | None = None,
                 ignore_message_not_modified: bool,
                 message_process: MessageProcess = None,
                 callback_process: CallbackProcess = None,
                 **kwargs):
        super().__init__(_id, func, *args,
                         came_from_menu_id=came_from_menu_id,
                         ignore_message_not_modified=ignore_message_not_modified,
                         **kwargs)

        # hooked process
        self._message_process = self.process_wrapper(message_process)
        self._callback_process = self.process_wrapper(callback_process)

    def process_wrapper(self, process: Callable):
        if process is None:
            return

        async def inner(*_args, **_kwargs):
            try:
                return await process(*_args, **_kwargs)
            except MessageNotModified:
                if not self.ignore_message_not_modified:
                    raise
                return
            except UserIsBlocked:
                return
            except asyncio.exceptions.TimeoutError:
                return

        return inner

    @property
    def message_process(self) -> MessageProcess:
        return self._message_process

    @property
    def callback_process(self) -> CallbackProcess:
        return self._callback_process

    @message_process.setter
    def message_process(self, process: MessageProcess):
        self._message_process = self.process_wrapper(process)

    @callback_process.setter
    def callback_process(self, process: CallbackProcess):
        self._callback_process = self.process_wrapper(process)

    def has_message_process(self) -> bool:
        return self.message_process is not None

    def has_callback_process(self) -> bool:
        return self.callback_process is not None


class FuncMenu(Menu):
    pass
