import pandas as pd
from calculations import calculate_wr_age_score

def calculate_value(player):
    """ Value algorithm for players."""
    position = player["position"]

    if position == "WR":
        return calculate_wr_value(player)
    elif position == "RB":
        return calculate_rb_value(player)
    elif position == "QB":
        return calculate_qb_value(player)
    elif position == "TE":
        return calculate_te_value(player)
    return 0


def calculate_wr_value(player):
    """ Value algorithm for wide receivers. """
    production_score = (
        player["receptions_per_game"] * 17 +
        player["receiving_yards_per_game"] * 17 * 0.01 +
        player["rushing_yards_per_game"] * 17 * 0.01 +
        (player["receiving_tds_per_game"] + player["rushing_tds_per_game"]) * 17 * 6 
    )
    
    opportunity_score = (
        player["targets_per_game"] * 10
    )

    age = calculate_wr_age_score(player["age"])
    
    return production_score + opportunity_score + age 


def calculate_rb_value(player):
    """ Value algorithm for running backs. """
    production_score = (
        player["receptions_per_game"] * 17 +
        player["receiving_yards_per_game"] * 17 * 0.01 +
        player["rushing_yards_per_game"] * 17 * 0.01 +
        (player["receiving_tds_per_game"] + player["rushing_tds_per_game"]) * 17 * 6 
    )

    opportunity_score = (
        player["carries_per_game"] * 4 +
        player["targets_per_game"] * 8 
    )


    age = (player["age"] - 26) * -15
    
    return production_score + opportunity_score + age 


def calculate_te_value(player):
    """ Value algorithm for tight ends. """
    production_score = (
            player["receptions_per_game"] * 17 +
            player["receiving_yards_per_game"] * 17 * 0.01 +
            player["rushing_yards_per_game"] * 17 * 0.01 +
            (player["receiving_tds_per_game"] + player["rushing_tds_per_game"]) * 17 * 6 
        )
        
    opportunity_score = player["targets_per_game"] * 10

    age = (30 - player["age"]) * 10
        
    return production_score + opportunity_score + age


def calculate_qb_value(player):
    """ Value algorithm for quarterbacks. """
    production_score = (
        player["passing_yards_per_game"] * 17 * 0.04 +
        player["passing_tds_per_game"] * 17 * 4 +
        player["completions_per_game"] * 17 * 0.3 +
        player["interceptions_per_game"] * 17 * -1 +
        player["rushing_yards_per_game"] * 17 * 0.1 +
        player["rushing_tds_per_game"] * 17 * 6
    )

    
    opportunity_score = (
        player["attempts_per_game"] * 0.5 +
        player["carries_per_game"] * 2
    )
    
    age = (33 - player["age"]) * 5
    
    
    if player["name"] == "Brock Purdy":
        brock = 100
    else:
        brock = 0
    
    return (production_score + opportunity_score + age) / 2 + brock

# open csv files and combine them
wr_df = pd.read_csv("wr_player_data.csv")
rb_df = pd.read_csv("rb_player_data.csv")
te_df = pd.read_csv("te_player_data.csv")
qb_df = pd.read_csv("qb_player_data.csv")
df = pd.concat(
    [wr_df, rb_df, te_df, qb_df],
    ignore_index=True
)

# run calculate_value on every row and store it in a new 'value' column
df["value"] = df.apply(calculate_value, axis=1)

# save the updated table back to the csv file
df.to_csv("player_data.csv", index=False)

# order players by value
print(df[["name","position","value"]].sort_values(by="value", ascending=False))


# sort by value and reset index so it starts from 0 for the rankings
sorted_df = df.sort_values(by="value", ascending=False).reset_index(drop=True) 

sorted_df["rank"] = sorted_df.index + 1 # add rank column, index starts at 0 so add 1

rankings = sorted_df[[
    "rank",
    "name",
    "position",
    "team",
    "age",
    "points_per_game",
    "value"
]]

rankings.to_csv("player_rankings.csv", index=False)

# positional rankings
#wr
df[df["position"] == "WR"].sort_values(by="value", ascending=False).to_csv("wr_rankings.csv", index=False)
#rb
df[df["position"] == "RB"].sort_values(by="value", ascending=False).to_csv("rb_rankings.csv", index=False)
#qb
df[df["position"] == "QB"].sort_values(by="value", ascending=False).to_csv("qb_rankings.csv", index=False)
#te
df[df["position"] == "TE"].sort_values(by="value", ascending=False).to_csv("te_rankings.csv", index=False)