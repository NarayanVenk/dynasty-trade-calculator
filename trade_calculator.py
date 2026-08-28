import pandas as pd
from calculations import normalize_player_name

# load player values
df = pd.read_csv("player_data.csv")

def get_player_value(player_name: str) -> float:
    """Get a player's calculated dynasty value by name"""

    player = df[df["name"].apply(normalize_player_name) == normalize_player_name(player_name)]

    if player.empty:
        raise ValueError(f"Player not found: {player_name}")

    return float(player.iloc[0]["value"])   # instead of returning the DataFrame, use iloc[0] to return the first row in the value column

print(get_player_value("Luther Burden"))
print(get_player_value("Luther Burden III"))
print(get_player_value("Justin Jefferson"))