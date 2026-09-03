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

def get_round_name(round_number: int) -> str:
    """Convert a draft round number to its st or th name"""
    if round_number == 1:
        return "1st"
    elif round_number == 2:
        return "2nd"
    elif round_number == 3:
        return "3rd"
    else:
        return f"{round_number}th"

def get_pick_values():
    """Get dynasty draft pick values from Stats Guy."""

    url = "https://api.statsguyfantasy.com/api/v1/picks"

    response = requests.get(url)

    response.raise_for_status()

    # convert the json into a dictionary
    data = response.json()

    # dictionary that stores pick name as the key and 'value' as the value
    pick_values = {}

    for pick in data["picks"]:
        year = pick["year"]
        round_number = pick["round"]
        value = pick["value"]["non_sf_dynasty"]

        # change the API data into a normal format:

        # if they specify actual slot, format it like 1.01 instead of round 1 slot 1
        if "slot" in pick:
            slot = pick["slot"]
            name = f"{year} {round_number}.{slot:02d}"  #02d means always format the integer using at least two digits so you dont end up with 1.1 when you want 1.01

        # otherwise it should be early, mid, or late
        else:
            variant = pick["variant"]
            round_name = get_round_name(round_number)
            name = f"{year} {variant} {round_name}"

        pick_values[name] = value

    return pick_values

pick_values = get_pick_values()

print(pick_values["2026 1.01"])
print(pick_values["2026 1.12"])
print(pick_values["2027 early 1st"])
print(pick_values["2027 mid 1st"])
print(pick_values["2027 late 1st"])
print(pick_values["2028 early 2nd"])