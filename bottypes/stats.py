from abc import ABC, abstractmethod
from dataclasses import dataclass, fields


class Statistic(ABC):  # yes, I'm a ~~crazy idiot~~ silly cat
    _value = None

    def __init__(self):
        if self._value is None:
            raise ValueError(f'initial value (_value) for {self.__class__.__name__} not assigned')
        self._type = type(self._value)

    def __get__(self, instance, owner=None):
        return self._value

    def __set__(self, instance, value):
        if not isinstance(value, self._type):
            raise TypeError(f'Wrong type of value, expected {self._type.__name__}, got {value.__class__.__name__}')
        self._value = value

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def clear(self):
        raise NotImplementedError


class StatisticInt(Statistic):
    _value = 0

    def __call__(self):
        self._value += 1

    def clear(self):
        self._value = 0


class StatisticList(Statistic):
    _value = []

    def __call__(self, value):
        self._value.append(value)

    def clear(self):
        self._value = []


@dataclass(slots=True)
class BotRegularStats:
    callback_queries_handled = StatisticInt()
    inline_queries_handled = StatisticInt()
    unique_users_served = StatisticList()
    exceptions_caught = StatisticInt()

    def clear(self):
        for field in fields(self):
            getattr(self, field.name).clear()
