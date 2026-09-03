import pandas as pd
from calculations import normalize_player_name

# load player values
df = pd.read_csv("player_data.csv")

# draft pick values
PICK_VALUES = {
    "2027 1st": 250,
    "2027 2nd": 100,
    "2027 3rd": 40
}

def get_player_value(player_name: str) -> float:
    """Get a player's calculated dynasty value by name"""

    player = df[df["name"].apply(normalize_player_name) == normalize_player_name(player_name)]

    if player.empty:
        raise ValueError(f"Player not found: {player_name}")

    return float(player.iloc[0]["value"])   # instead of returning the DataFrame, use iloc[0] to return the first row in the value column

def get_asset_value(asset: str) -> float:
    """Determine if an asset is a player or pick and get its value"""
    if asset in PICK_VALUES:
        return PICK_VALUES[asset]
    return get_player_value(asset)

def calculate_trade(side_a: list[str], side_b: list[str]):
    """Compare the total value of two sides of a trade"""

    side_a_value= sum(get_asset_value(asset) for asset in side_a)
    
    side_b_value= sum(get_asset_value(asset) for asset in side_b)

    # calculate the value differnce in the trade
    difference = abs(side_a_value - side_b_value)

    print("Side A:")
    for asset in side_a:
        print(asset + ":", round(get_asset_value(asset), 2))

    print("Side A total:", round(side_a_value, 2))

    print("\nSide B:")
    for asset in side_b:
        print(asset + ":", round(get_asset_value(asset), 2))

    print("Side B total:", round(side_b_value, 2))

    if side_a_value > side_b_value:
        print("\nSide A has", round(difference, 2), "more value")

    elif side_b_value > side_a_value:
        print("\nSide B has", round(difference, 2), "more value")
    else:
        print("\nThe trade is even")


side_a = [
    "Justin Jefferson",
    "James Cook"
]

side_b = [
    "Ja'Marr Chase",
    "2027 1st"
]

calculate_trade(side_a, side_b)