from pyrogram.types import (CallbackGame,
                            InlineKeyboardButton,
                            InlineKeyboardMarkup,
                            LoginUrl,
                            WebAppInfo)

from l10n import Locale


class ExtendedIKB(InlineKeyboardButton):
    SELECTION_INDICATOR = '•'

    def __init__(self,
                 text: str,
                 callback_data: str | bytes = None,
                 url: str = None,
                 web_app: WebAppInfo = None,
                 login_url: LoginUrl = None,
                 user_id: int = None,
                 switch_inline_query: str = None,
                 switch_inline_query_current_chat: str = None,
                 callback_game: CallbackGame = None,
                 *,
                 translatable: bool = True,
                 selectable: bool = True):
        if callback_data is None and url is None:
            callback_data = text

        super().__init__(text, callback_data, url, web_app, login_url, user_id,
                         switch_inline_query, switch_inline_query_current_chat, callback_game)
        self.translatable = translatable
        self.selectable = selectable

        self.text_key = self.text
        self.url_key = None
        self.selected = False
        if self.url:
            self.url_key = self.url

    def set_localed_text(self, locale: Locale):
        if self.translatable:
            self.text = locale.get(self.text_key)
            if self.url_key:
                self.url = locale.get(self.url_key)
        else:
            self.text = self.text_key

        if self.selectable and self.selected:
            self.text = f'{self.SELECTION_INDICATOR} {self.text} {self.SELECTION_INDICATOR}'

    def localed(self, locale: Locale):
        self.set_localed_text(locale)
        return self

    def __call__(self, locale: Locale):
        return self.localed(locale)


class ExtendedIKM(InlineKeyboardMarkup):
    def update_locale(self, locale: Locale):
        for line in self.inline_keyboard:
            for button in line:
                if isinstance(button, ExtendedIKB):
                    button.set_localed_text(locale)

    def localed(self, locale: Locale):
        self.update_locale(locale)
        return self

    def __call__(self, locale: Locale):
        return self.localed(locale)

    def select_button_by_key(self, key: str):
        for line in self.inline_keyboard:
            for button in line:
                if isinstance(button, ExtendedIKB) and button.selectable:
                    if button.text_key == key or button.callback_data == key:
                        button.selected = True
                    else:
                        button.selected = False  # only one button at a time can be selected
