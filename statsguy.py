import requests



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
        rankings[player["name"]] = player["value"]

    return rankings

# create the dictionary
wr_market_rankings = get_market_rankings("WR")
rb_market_rankings = get_market_rankings("RB")
te_market_rankings = get_market_rankings("TE")
qb_market_rankings = get_market_rankings("QB")

# prints the player's ranking
print(wr_market_rankings["Justin Jefferson"])
print(wr_market_rankings["Zay Flowers"])
print(wr_market_rankings["Luther Burden"])
print(rb_market_rankings["Omarion Hampton"])
print(rb_market_rankings["Javonte Williams"])
print(te_market_rankings["Trey McBride"])
print(qb_market_rankings["Josh Allen"])
