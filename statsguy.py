import requests
from calculations import normalize_player_name


def get_market_rankings(position: str):
    """Get Stats Guy Fantasy dynasty market rankings for a position."""

    url = "https://api.statsguyfantasy.com/api/v1/rankings"

    response = requests.get(
        url,
        params={
            "format": "non_sf_dynasty",
            "position": position,
            "limit": 1000
        }
    )

    # raise an exception and stop if anything goes wrong
    response.raise_for_status()

    # convert the json into a dictionary
    data = response.json()

    # dictionary that stores name as the key and 'value' as the value
    rankings = {}

    for player in data["rankings"]:
        name = normalize_player_name(player["name"])
        rankings[name] = player["value"]

    return rankings

