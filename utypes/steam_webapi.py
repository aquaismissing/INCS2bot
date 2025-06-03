import requests


class SteamWebAPI:
    """Made because `steamio` doesn't have any Steam WebAPI support."""
    # todo: deprecate and finish making it into seperate package
    # todo: maybe even without API methods for partners (since we can't test them properly anyway)

    BASE_URL = 'api.steampowered.com'
    DEFAULT_HEADERS = {}
    DEFAULT_TIMEOUT = 15

    def __init__(self, api_key: str, *, headers: dict = None, timeout: int = None):
        self.api_key = api_key
        self.headers = headers or self.DEFAULT_HEADERS
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.session = requests.Session()

    def _method(self, interface: str, method: str, version: int, params: dict = None):  # only supports GET methods btw
        params = params.copy() if params else {}
        params['key'] = self.api_key

        response = self.session.get(
            f'https://{self.BASE_URL}/{interface}/{method}/v{version}/',
            params=params,
            headers=self.headers,
            timeout=self.timeout
        )

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            return response

    def close(self):
        self.session.close()

    def get_player_bans(self, steamids: list | tuple | str):
        if isinstance(steamids, (list, tuple)):
            steamids = ','.join(steamids)

        return self._method('ISteamUser', 'GetPlayerBans', 1,
                            {'steamids': steamids})

    def get_player_summaries(self, steamids: list | tuple | str):
        if isinstance(steamids, (list, tuple)):
            steamids = ','.join(steamids)

        return self._method('ISteamUser', 'GetPlayerSummaries', 2,
                            {'steamids': steamids})

    def get_user_game_stats(self, steamid: str | int, appid: int):
        if isinstance(steamid, int):
            steamid = str(steamid)

        return self._method('ISteamUserStats', 'GetUserStatsForGame', 2,
                            {'steamid': steamid, 'appid': appid})

    def get_asset_prices(self, appid: int):
        return self._method('ISteamEconomy', 'GetAssetPrices', 1,
                            {'appid': appid})

    def get_number_of_current_players(self, appid: int):
        return self._method('ISteamUserStats', 'GetNumberOfCurrentPlayers', 1,
                            {'appid': appid})

    def csgo_get_monthly_player_count(self):
        response = self._method('ICSGOServers_730', 'GetMonthlyPlayerCount', 1)
        return int(response['result']['players'])

    def csgo_get_game_servers_status(self):
        return self._method('ICSGOServers_730', 'GetGameServersStatus', 1)
