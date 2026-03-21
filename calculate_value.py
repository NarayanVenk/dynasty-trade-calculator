import pandas as pd


def calculate_value(row):
    """ Value algorithm for players. """
    return (
        row["fantasy_points"] * 0.6 +
        row["points_per_game"] * 0.2 +
        (30 - row["age"]) * 1.5
    )


# open csv file and convert it into a table
df = pd.read_csv("player_data.csv")

# run calculate_value on every row and store it in a new 'value' column
df["value"] = df.apply(calculate_value, axis=1)

# save the updated table back to the csv file
df.to_csv("player_data.csv", index=False)