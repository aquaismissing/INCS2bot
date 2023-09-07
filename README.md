# INCS2 Bot

###### Made with ❤️ by [@INCS2](https://t.me/INCS2)

Note: **this bot doesn't grant you access to CS2 Limited Test**,
the real purpose is to monitor and display game servers status and other useful information.

---

### Isn't it just CS:GO Beta Bot but rebranded?

Not really. 
We swapped from Telebot to Pyrogram to [get advantages of the MTProto API][mtproto api advantages], 
and most of the codebase was rewritten to be more modular and perfomant. 

### Any changes?

Most of the bot functionality stays the same.
However, here are some noteworthy changes:
- Bot now uses inline keyboards instead of reply ones
- Most of the bot messages stay in one, reducing the clutter in messages
- More user-friendly approach for inline queries with the help of tags
- Personal settings (only language settings available for now)

Anyway, we have some plans on adding more functionality and QoL features.

### Internal changes?
 
- Complete restructuring of the project
- The bot handling was rewritten around Pyrogram
- Localization system, allowing us to have more than two languages
  and easily handle it at the same time
- Tags system, made for inline queries to be more responsive and user-friendly
- Extended Inline Keyboard Markups (**ExtendedIKM**s), 
  made to integrate extra functionality into regular **IKM**s (e.g. localization, selection indicators)
- Use of decorators to support transitions between menus and clean up the codebase

### How can I contribute?

For now, we don't actually need any help with developing the bot. \
However, you can help us translate it in different languages.
Navigate to [l10n/ folder](./l10n) to see more information.


[mtproto api advantages]: https://docs.pyrogram.org/topics/mtproto-vs-botapi#advantages-of-the-mtproto-api