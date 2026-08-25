import nflreadpy as nfl
from datetime import date
import polars as pl
from calculations import calculate_age, calculate_per_game, calculate_season_weight

current_year = date.today().year
last_season = current_year - 1

WR_SEASON_WEIGHTS = {
    last_season: 0.50,
    last_season - 1: 0.30,
    last_season - 2: 0.20
}

players = nfl.load_players()

# using polars to create a dataframe and filter for only the 4 relevant fantasy positions and players in the current season
fantasy_players = players.filter(players["position"].is_in(["QB", "RB", "WR", "TE"]) & (players["last_season"] == current_year))

# create a stats dataframe and filter for last 3 seasons
stats = nfl.load_player_stats(
    seasons = [last_season - 2, last_season - 1, last_season],
    summary_level = "reg"
)


# create another dataframe that joins the fantasy_players table and their stats with a left join so rookies remain (as their stat values will be 0)
# player_data = fantasy_players.join(
#     stats,
#     left_on="gsis_id",
#     right_on="player_id",
#     how="left"
# )

# Convert birth_date strings into actual dates
# player_data = player_data.with_columns(
#     pl.col("birth_date")
#     .str.to_date("%Y-%m-%d", strict=False)
#     .alias("birth_date")
# )

# add two columns, age and points_per_game
# player_data = player_data.with_columns(
#     # calculate the age of every player in the dataset using map_elements
#     age = pl.col("birth_date").map_elements(calculate_age, return_dtype=pl.Float64),

#     # calculate the points per game of every player in the dataset using a lambda to take in both fantasy points and games
#     points_per_game = pl.struct( ["fantasy_points_ppr", "games"]).map_elements(
#         lambda row: calculate_per_game(row["fantasy_points_ppr"], row["games"]), return_dtype=pl.Float64)
# )

# select the columns we need and change the names using alias so that the existing value calculation works
# player_data = player_data.select([
#     pl.col("gsis_id"),
#     pl.col("display_name").alias("name"),
#     pl.col("position"),
#     pl.col("latest_team").alias("team"),
#     pl.col("age"),

#     pl.col("games").alias("games_played"),
#     pl.col("points_per_game"),

#     pl.col("receptions"),
#     pl.col("receiving_yards"),
#     pl.col("receiving_tds"),
#     pl.col("targets"),

#     pl.col("carries").alias("rush_attempts"),
#     pl.col("rushing_yards"),
#     pl.col("rushing_tds"),

#     pl.col("completions"),
#     pl.col("attempts").alias("pass_attempts"),
#     pl.col("passing_yards"),
#     pl.col("passing_tds"),
#     pl.col("passing_interceptions").alias("interceptions")
# ])

# WR-only tables
wrs = fantasy_players.filter(
    pl.col("position") == "WR"
)

wr_stats = stats.filter(
    pl.col("position") == "WR"
)

# attach the rookie season of the wr so we know which seasons should count
wr_stats = wr_stats.join(wrs.select(
    ["gsis_id", "rookie_season"]),
        left_on = "player_id",
        right_on="gsis_id",
        how="inner"
)

# calculate the per-game values for every season separately
wr_stats = wr_stats.with_columns(
    receptions_per_game=pl.struct(
        ["receptions", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["receptions"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    targets_per_game=pl.struct(
        ["targets", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["targets"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    receiving_yards_per_game=pl.struct(
        ["receiving_yards", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["receiving_yards"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    receiving_tds_per_game=pl.struct(
        ["receiving_tds", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["receiving_tds"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    rushing_yards_per_game=pl.struct(
        ["rushing_yards", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["rushing_yards"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    rushing_tds_per_game=pl.struct(
        ["rushing_tds", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["rushing_tds"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    points_per_game=pl.struct(
        ["fantasy_points_ppr", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["fantasy_points_ppr"],
            row["games"]
        ),
        return_dtype=pl.Float64
    )
)

# add the season weights
wr_stats = wr_stats.with_columns(
    season_weight=pl.struct(
        ["season", "rookie_season"]
    ).map_elements(
        lambda row: calculate_season_weight(
            row["season"],
            row["rookie_season"],
            WR_SEASON_WEIGHTS
        ),
        return_dtype=pl.Float64
    )
)

# multiply each per game stat by that season's weight
wr_stats = wr_stats.with_columns(
    weighted_receptions_per_game=(
        pl.col("receptions_per_game") * pl.col("season_weight")
    ),

    weighted_targets_per_game=(
        pl.col("targets_per_game") * pl.col("season_weight")
    ),

    weighted_receiving_yards_per_game=(
        pl.col("receiving_yards_per_game") * pl.col("season_weight")
    ),

    weighted_receiving_tds_per_game=(
        pl.col("receiving_tds_per_game") * pl.col("season_weight")
    ),

    weighted_rushing_yards_per_game=(
        pl.col("rushing_yards_per_game") * pl.col("season_weight")
    ),

    weighted_rushing_tds_per_game=(
        pl.col("rushing_tds_per_game") * pl.col("season_weight")
    ),

    weighted_points_per_game=(
        pl.col("points_per_game") * pl.col("season_weight")
    )
)

# at this point we have a table that contains the year and weighted per game stats for that year for each player
# collapse the three seasons back into one row per WR by adding each weighted per games together
wr_weighted_stats = wr_stats.group_by("player_id").agg(
    pl.col("weighted_receptions_per_game")
        .sum()
        .alias("receptions_per_game"),

    pl.col("weighted_targets_per_game")
        .sum()
        .alias("targets_per_game"),

    pl.col("weighted_receiving_yards_per_game")
        .sum()
        .alias("receiving_yards_per_game"),

    pl.col("weighted_receiving_tds_per_game")
        .sum()
        .alias("receiving_tds_per_game"),

    pl.col("weighted_rushing_yards_per_game")
        .sum()
        .alias("rushing_yards_per_game"),

    pl.col("weighted_rushing_tds_per_game")
        .sum()
        .alias("rushing_tds_per_game"),

    pl.col("weighted_points_per_game")
        .sum()
        .alias("points_per_game")
)
                
# join the weighted stats back to wrs
wr_player_data = wrs.join(
    wr_weighted_stats,
    left_on="gsis_id",
    right_on="player_id",
    how="left"
)

# convert birth_date string into actual dates
wr_player_data = wr_player_data.with_columns(
    pl.col("birth_date")
    .str.to_date("%Y-%m-%d", strict=False)
    .alias("birth_date")
)

# calculate age using map_elements
wr_player_data = wr_player_data.with_columns(
    age=pl.col("birth_date").map_elements(
        calculate_age,
        return_dtype=pl.Float64
    )
)

# select only what is needed for the WR model
wr_player_data = wr_player_data.select([
    pl.col("gsis_id"),
    pl.col("display_name").alias("name"),
    pl.col("position"),
    pl.col("latest_team").alias("team"),
    pl.col("age"),

    pl.col("receptions_per_game"),
    pl.col("targets_per_game"),
    pl.col("receiving_yards_per_game"),
    pl.col("receiving_tds_per_game"),
    pl.col("rushing_yards_per_game"),
    pl.col("rushing_tds_per_game"),
    pl.col("points_per_game")
])

# fill any null columns with 0
wr_player_data = wr_player_data.fill_null(0)

# save into a separate wr player data csv
wr_player_data.write_csv("wr_player_data.csv")

# fill any null columns with 0
# player_data = player_data.with_columns(
#     [pl.col(column).fill_null(0) for column in stat_columns]
# )

# # save the data to the csv
# player_data.write_csv("player_data.csv")