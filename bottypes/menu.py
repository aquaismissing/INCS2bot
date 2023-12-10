class Menu:
    def __init__(self,
                 _id: str,
                 func: callable,
                 *args,
                 came_from_menu_id: str | None = None,
                 ignore_message_not_modified: bool,
                 message_process: callable = None,
                 callback_process: callable = None,
                 **kwargs):
        self.id = _id

        # menu functionality
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.came_from_menu_id = came_from_menu_id

        # hooked process
        self.message_process = message_process
        self.callback_process = callback_process

        # utils
        self.ignore_message_not_modified = ignore_message_not_modified

    async def __call__(self, *args, **kwargs):
        return await self.func(*args, *self.args, **kwargs, **self.kwargs)

    def __repr__(self):
        return f'<{self.__class__.__name__}(id={self.id}, func={self.func})>'

    def has_message_process(self) -> bool:
        return self.message_process is not None

    def has_callback_process(self) -> bool:
        return self.callback_process is not None

    def can_come_from(self, _id):
        return self.came_from_menu_id == _id


class NavMenu(Menu):
    pass


class FuncMenu(Menu):
    pass
