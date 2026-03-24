import pandas as pd


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
    games = max(player["games_played"], 1)  # prevent division by zero

    production_score = (
        player["receptions"] * 1 +
        player["receiving_yards"] * 0.01 +
        player["rushing_yards"] * 0.01 +
        (player["receiving_tds"] + player["rushing_tds"]) * 6 
    )
    
    opportunity_score = (
        (player["targets"] / games) * 1.0
    )

    age = (30 - player["age"]) * 10
    
    output = player["points_per_game"] * 4
    
    return production_score + opportunity_score + age + output


def calculate_rb_value(player):
    """ Value algorithm for running backs. """
    games = max(player["games_played"], 1)

    production_score = (
        player["receptions"] * 1 +
        player["receiving_yards"] * 0.01 +
        player["rushing_yards"] * 0.01 +
        (player["receiving_tds"] + player["rushing_tds"]) * 6 
    )

    opportunity_score = (
        (player["rush_attempts"] / games) * 1 +
        (player["targets"] / games) * 1
    )


    age = (player["age"] - 26) * -15
 
    output = player["points_per_game"] * 4
    
    return production_score + opportunity_score + age + output


def calculate_te_value(player):
    """ Value algorithm for tight ends. """
    games = max(player["games_played"], 1)

    production_score = (
        player["receptions"] * 1 +
        player["receiving_yards"] * 0.01 +
        player["rushing_yards"] * 0.01 +
        (player["receiving_tds"] + player["rushing_tds"]) * 6 
    )
    
    opportunity_score = (
        (player["targets"] / games) * 2
    )
    
    age = (30 - player["age"]) * 10
    
    output = player["points_per_game"] * 4

    return production_score + opportunity_score + age + output


def calculate_qb_value(player):
    """ Value algorithm for quarterbacks. """
    games = max(player["games_played"], 1)

    production_score = (
        player["passing_yards"] * 0.04 +
        player["passing_tds"] * 4 +
        player["completions"] * 0.3 +
        player["interceptions"] * -1 +
        player["rushing_yards"] * 0.1 +
        player["rushing_tds"] * 6 
    )
    
    opportunity_score = (
        (player["pass_attempts"] / games) * 0.5 +
        (player["rush_attempts"] / games) * 2 
    )
    
    age = (33 - player["age"]) * 10
    
    output = player["points_per_game"] * 4
    
    if player["name"] == "Brock Purdy":
        brock = 100
    else:
        brock = 0
    
    return (production_score + opportunity_score + age + output + brock) / 2

# open csv file and convert it into a table
df = pd.read_csv("player_data.csv")

# run calculate_value on every row and store it in a new 'value' column
df["value"] = df.apply(calculate_value, axis=1)

# save the updated table back to the csv file
df.to_csv("player_data.csv", index=False)

# order players by value
print(df[["name","position","value"]].sort_values(by="value", ascending=False))