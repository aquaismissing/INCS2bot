from dataclasses import dataclass, fields


@dataclass(slots=True)
class BotRegularStats:
    callback_queries_handled: int = 0
    inline_queries_handled: int = 0
    unique_users_served: int = 0
    exceptions_caught: int = 0

    def clear(self):
        for field in fields(self):
            setattr(self, field.name, 0)
