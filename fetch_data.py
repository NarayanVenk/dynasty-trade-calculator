import nflreadpy as nfl
from datetime import date
import polars as pl
from calculations import calculate_age, calculate_points_per_game

current_year = date.today().year
players = nfl.load_players()

# using polars to create a dataframe and filter for only the 4 relevant fantasy positions and players in the current season
fantasy_players = players.filter(players["position"].is_in(["QB", "RB", "WR", "TE"]) & (players["last_season"] == current_year))

# select which columns we want printed
print(fantasy_players.select([
    "gsis_id",
    "display_name",
    "position",
    "latest_team",
    "birth_date",
    "status",
    "rookie_season",
    "last_season",
    "draft_year",
    "draft_round",
    "draft_pick"
]).head(25))

# create a stats dataframe and filter for 2025 stats for now
stats = nfl.load_player_stats(
    seasons = [2025],
    summary_level = "reg"
)


# create another dataframe that joins the fantasy_players table and their stats with a left join so rookies remain (as their stat values will be 0)
player_data = fantasy_players.join(
    stats,
    left_on="gsis_id",
    right_on="player_id",
    how="left"
)

# Convert birth_date strings into actual dates
player_data = player_data.with_columns(
    pl.col("birth_date")
    .str.to_date("%Y-%m-%d", strict=False)
    .alias("birth_date")
)

# add two columns, age and points_per_game
player_data = player_data.with_columns(
    # calculate the age of every player in the dataset using map_elements
    age = pl.col("birth_date").map_elements(calculate_age, return_dtype=pl.Float64),

    # calculate the points per game of every player in the dataset using a lambda to take in both fantasy points and games
    points_per_game = pl.struct( ["fantasy_points_ppr", "games"]).map_elements(
        lambda row: calculate_points_per_game(row["fantasy_points_ppr"], row["games"]), return_dtype=pl.Float64)
)

# select the columns we need and change the names using alias so that the existing value calculation works
player_data = player_data.select([
    pl.col("gsis_id"),
    pl.col("display_name").alias("name"),
    pl.col("position"),
    pl.col("latest_team").alias("team"),
    pl.col("age"),

    pl.col("games").alias("games_played"),
    pl.col("points_per_game"),

    pl.col("receptions"),
    pl.col("receiving_yards"),
    pl.col("receiving_tds"),
    pl.col("targets"),

    pl.col("carries").alias("rush_attempts"),
    pl.col("rushing_yards"),
    pl.col("rushing_tds"),

    pl.col("completions"),
    pl.col("attempts").alias("pass_attempts"),
    pl.col("passing_yards"),
    pl.col("passing_tds"),
    pl.col("passing_interceptions").alias("interceptions")
])

# list of stat columns where any missing values should be treated as 0
stat_columns = [
    "games_played",
    "points_per_game",
    "receptions",
    "receiving_yards",
    "receiving_tds",
    "targets",
    "rush_attempts",
    "rushing_yards",
    "rushing_tds",
    "completions",
    "pass_attempts",
    "passing_yards",
    "passing_tds",
    "interceptions"
]

# fill any null columns with 0
player_data = player_data.with_columns(
    [pl.col(column).fill_null(0) for column in stat_columns]
)

# save the data to the csv
player_data.write_csv("player_data.csv")