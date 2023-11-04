from dataclasses import dataclass, fields


class StatisticInt:  # for now just int descriptor
    value = 0        # maybe make a generic one?

    def __get__(self, instance, owner=None):
        return self.value

    def __set__(self, instance, value):
        self.value = value

    def __call__(self):
        self.value += 1

    def clear(self):
        self.value = 0


@dataclass(slots=True)
class BotRegularStats:
    callback_queries_handled = StatisticInt()
    inline_queries_handled = StatisticInt()
    unique_users_served = StatisticInt()
    exceptions_caught = StatisticInt()

    def clear(self):
        for field in fields(self):
            getattr(self, field.name).clear()
