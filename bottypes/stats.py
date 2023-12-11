from dataclasses import dataclass


@dataclass
class BotRegularStats:
    callback_queries_handled = 0
    inline_queries_handled = 0
    unique_users_served = set()
    exceptions_caught = 0

    def clear(self):
        self.callback_queries_handled = 0
        self.inline_queries_handled = 0
        self.unique_users_served = set()
        self.exceptions_caught = 0
