class Menu:
    def __init__(self,
                 _id: str,
                 func: callable,
                 *args,
                 came_from_menu_id: str | None = None,
                 ignore_message_not_modified: bool,
                 callback_process: callable = None,
                 **kwargs):
        self.id = _id

        # menu functionality
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.came_from_menu_id = came_from_menu_id

        # hooked process
        self.callback_process = callback_process

        # utils
        self.ignore_message_not_modified = ignore_message_not_modified

    def __call__(self, *args, **kwargs):
        return self.func(*args, *self.args, **kwargs, **self.kwargs)

    def __repr__(self):
        return f'<{self.__class__.__name__}(func={self.func})>'

    def has_callback_process(self) -> bool:
        return self.callback_process is not None


class NavMenu(Menu):
    pass


class FuncMenu(Menu):
    pass
