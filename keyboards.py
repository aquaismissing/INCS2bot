from pyrogram.types import (InlineKeyboardMarkup,
                            InlineKeyboardButton,
                            ReplyKeyboardRemove)

from l10n import Locale, LocaleKeys as LK


class TranslatableIKB(InlineKeyboardButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text_key = self.text
        self.url_key = None
        if self.url:
            self.url_key = self.url

    def set_localed_text(self, locale: Locale):
        self.text = locale.get(self.text_key)
        if self.url_key:
            self.url = locale.get(self.url_key)

    def localed(self, locale: Locale):
        self.set_localed_text(locale)
        return self

    def __call__(self, locale: Locale):
        return self.localed(locale)


class TranslatableIKM(InlineKeyboardMarkup):
    def update_locale(self, locale: Locale):
        for line in self.inline_keyboard:
            for button in line:
                if isinstance(button, TranslatableIKB):
                    button.set_localed_text(locale)

    def localed(self, locale: Locale):
        self.update_locale(locale)
        return self

    def __call__(self, locale: Locale):
        return self.localed(locale)


# Delete keyboard
markup_del = ReplyKeyboardRemove(False)

# Back button
back_button = TranslatableIKB(LK.bot_back, LK.bot_back)

# Channel link for inline messages
inline_button_channel_link = TranslatableIKB(LK.bot_author_text, url=LK.bot_author_link)

markup_inline_button = TranslatableIKM([[inline_button_channel_link]])

# Default
server_stats = TranslatableIKB(LK.bot_servers_stats, LK.bot_servers_stats)
profile_info = TranslatableIKB(LK.bot_profile_info, LK.bot_profile_info)
extra_features = TranslatableIKB(LK.bot_extras, LK.bot_extras)

main_markup = TranslatableIKM([
    [server_stats],
    [profile_info],
    [extra_features]
])

# Server Statistics
server_status = TranslatableIKB(LK.game_status_button_title, LK.game_status_button_title)
matchmaking = TranslatableIKB(LK.stats_matchmaking_button_title, LK.stats_matchmaking_button_title)
dc = TranslatableIKB(LK.dc_status_title, LK.dc_status_title)

markup_ss = TranslatableIKM([
    [server_status],
    [matchmaking],
    [dc],
    [back_button]
])


# Profile Information
profile_info = TranslatableIKB(LK.user_profileinfo_title, LK.user_profileinfo_title)
cs_stats = TranslatableIKB(LK.user_gamestats_button_title, LK.user_gamestats_button_title)

markup_profile = TranslatableIKM([
    [profile_info],
    [cs_stats],
    [back_button]
])

# Extra Features

crosshair = TranslatableIKB(LK.crosshair, LK.crosshair)
currency = TranslatableIKB(LK.exchangerate_button_title, LK.exchangerate_button_title)
valve_hq_time = TranslatableIKB(LK.valve_hqtime_button_title, LK.valve_hqtime_button_title)
timer = TranslatableIKB(LK.game_dropcap_button_title, LK.game_dropcap_button_title)
game_version = TranslatableIKB(LK.game_version_button_title, LK.game_version_button_title)
guns = TranslatableIKB(LK.gun_button_text, LK.gun_button_text)

markup_extra = TranslatableIKM([
    [crosshair, currency, game_version],
    [valve_hq_time, timer],
    [guns],
    [back_button]
])

# DC

europe = TranslatableIKB(LK.dc_europe, LK.dc_europe)
asia = TranslatableIKB(LK.dc_asia, LK.dc_asia)
africa = TranslatableIKB(LK.dc_africa, LK.dc_africa)
south_america = TranslatableIKB(LK.dc_southamerica, LK.dc_southamerica)
australia = TranslatableIKB(LK.dc_australia, LK.dc_australia)
us = TranslatableIKB(LK.dc_us, LK.dc_us)

markup_dc = TranslatableIKM([
    [asia, australia, europe],
    [africa, south_america, us],
    [back_button]
])

# DC Asia

india = TranslatableIKB(LK.dc_india, LK.dc_india)
emirates = TranslatableIKB(LK.dc_emirates, LK.dc_emirates)
china = TranslatableIKB(LK.dc_china, LK.dc_china)
singapore = TranslatableIKB(LK.dc_singapore, LK.dc_singapore)
hongkong = TranslatableIKB(LK.dc_hongkong, LK.dc_hongkong)
japan = TranslatableIKB(LK.dc_japan, LK.dc_japan)
south_korea = TranslatableIKB(LK.dc_southkorea, LK.dc_southkorea)

markup_dc_asia = TranslatableIKM([
    [china, emirates, hongkong],
    [south_korea, india],
    [japan, singapore],
    [back_button]
])

# DC Europe

eu_west = TranslatableIKB(LK.dc_west, LK.dc_eu_west)
eu_east = TranslatableIKB(LK.dc_east, LK.dc_eu_east)
eu_north = TranslatableIKB(LK.dc_north, LK.dc_eu_north)

markup_dc_eu = TranslatableIKM([
    [eu_east, eu_north, eu_west],
    [back_button]
])

# DC USA

us_northwest = TranslatableIKB(LK.dc_north, LK.dc_us_north)
us_southwest = TranslatableIKB(LK.dc_south, LK.dc_us_south)

markup_dc_us = TranslatableIKM([
    [us_northwest, us_southwest],
    [back_button]
])

# Guns

pistols = TranslatableIKB(LK.gun_pistols, LK.gun_pistols)
heavy = TranslatableIKB(LK.gun_heavy, LK.gun_heavy)
smgs = TranslatableIKB(LK.gun_smgs, LK.gun_smgs)
rifles = TranslatableIKB(LK.gun_rifles, LK.gun_rifles)

markup_guns = TranslatableIKM([
    [pistols, heavy],
    [smgs, rifles],
    [back_button]
])

# Pistols

usps = InlineKeyboardButton("USP-S", "usps")
p2000 = InlineKeyboardButton("P2000", "p2000")
glock = InlineKeyboardButton("Glock-18", "glock18")
dualies = InlineKeyboardButton("Dual Berettas", "dualberettas")
p250 = InlineKeyboardButton("P250", "p250")
cz75 = InlineKeyboardButton("CZ75-Auto", "cz75auto")
five_seven = InlineKeyboardButton("Five-SeveN", "fiveseven")
tec = InlineKeyboardButton("Tec-9", "tec9")
deagle = InlineKeyboardButton("Desert Eagle", "deserteagle")
r8 = InlineKeyboardButton("R8 Revolver", "r8revolver")

markup_pistols = TranslatableIKM([
    [usps, p2000, glock],
    [dualies, p250],
    [five_seven, tec, cz75],
    [deagle, r8],
    [back_button]
])

# Heavy

nova = InlineKeyboardButton("Nova", "nova")
xm1014 = InlineKeyboardButton("XM1014", "xm1014")
mag7 = InlineKeyboardButton("MAG-7", "mag7")
sawedoff = InlineKeyboardButton("Sawed-Off", "sawedoff")
m249 = InlineKeyboardButton("M249", "m249")
negev = InlineKeyboardButton("Negev", "negev")

markup_heavy = TranslatableIKM([
    [nova, xm1014],
    [mag7, sawedoff],
    [m249, negev],
    [back_button],
])

# SMGs

mp9 = InlineKeyboardButton("MP9", "mp9")
mac10 = InlineKeyboardButton("MAC-10", "mac10")
mp7 = InlineKeyboardButton("MP7", "mp7")
mp5 = InlineKeyboardButton("MP5-SD", "mp5sd")
ump = InlineKeyboardButton("UMP-45", "ump45")
p90 = InlineKeyboardButton("P90", "p90")
pp = InlineKeyboardButton("PP-Bizon", "ppbizon")

markup_smgs = TranslatableIKM([
    [mp9, mac10],
    [mp7, mp5],
    [ump, p90, pp],
    [back_button]
])

# Rifles

famas = InlineKeyboardButton("FAMAS", "famas")
galil = InlineKeyboardButton("Galil AR", "galilar")
m4a4 = InlineKeyboardButton("M4A4", "m4a4")
m4a1 = InlineKeyboardButton("M4A1-S", "m4a1s")
ak = InlineKeyboardButton("AK-47", "ak47")
aug = InlineKeyboardButton("AUG", "aug")
sg = InlineKeyboardButton("SG 553", "sg553")
ssg = InlineKeyboardButton("SSG 08", "ssg08")
awp = InlineKeyboardButton("AWP", "awp")
scar = InlineKeyboardButton("SCAR-20", "scar20")
g3sg1 = InlineKeyboardButton("G3SG1", "g3sg1")

markup_rifles = TranslatableIKM([
    [famas, galil],
    [m4a4, m4a1, ak],
    [aug, sg],
    [ssg, awp],
    [scar, g3sg1],
    [back_button]
])

# Crosshair
generate_crosshair = TranslatableIKB(LK.crosshair_generate, LK.crosshair_generate)
decode_crosshair = TranslatableIKB(LK.crosshair_decode, LK.crosshair_decode)

markup_crosshair = TranslatableIKM([
    [generate_crosshair, decode_crosshair],
    [back_button]
])
