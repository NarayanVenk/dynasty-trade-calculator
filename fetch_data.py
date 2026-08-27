import nflreadpy as nfl
from datetime import date
import polars as pl
from calculations import calculate_age, calculate_per_game, calculate_season_weight
from statsguy import get_market_rankings

current_year = date.today().year
last_season = current_year - 1

SEASON_WEIGHTS = {
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

# get dynasty market values for each position
wr_market = get_market_rankings("WR")
rb_market = get_market_rankings("RB")
te_market = get_market_rankings("TE")
qb_market = get_market_rankings("QB")

# WIDE RECEIVERS
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
            SEASON_WEIGHTS
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
# Example:
#player_id    season    rec/game    season_weight    weighted_rec/game
#Puka         2025       8.0           0.50               4.0
#Puka         2024       6.5           0.30               1.95
#Puka         2023       6.0           0.20               1.20
#4.00
#1.95
#1.20
#----
#7.15
#So, now we have:
#Puka    7.15 receptions_per_game
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

# add dynasty market value
wr_player_data = wr_player_data.with_columns(
    market_value=pl.col("name").map_elements(
        lambda name: wr_market.get(name, 0),
        return_dtype=pl.Int64
    )
)

# fill any null columns with 0
wr_player_data = wr_player_data.fill_null(0)

# save into a separate wr player data csv
wr_player_data.write_csv("wr_player_data.csv")

# RUNNING BACKS
# RB-only tables
rbs = fantasy_players.filter(
    pl.col("position") == "RB"
)

rb_stats = stats.filter(
    pl.col("position") == "RB"
)

# attach the rookie season of the rb so we know which seasons should count
rb_stats = rb_stats.join(rbs.select(
    ["gsis_id", "rookie_season"]),
        left_on = "player_id",
        right_on="gsis_id",
        how="inner"
)

# calculate the per-game values for every season separately
rb_stats = rb_stats.with_columns(
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

    carries_per_game=pl.struct(
        ["carries", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["carries"],
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
rb_stats = rb_stats.with_columns(
    season_weight=pl.struct(
        ["season", "rookie_season"]
    ).map_elements(
        lambda row: calculate_season_weight(
            row["season"],
            row["rookie_season"],
            SEASON_WEIGHTS
        ),
        return_dtype=pl.Float64
    )
)

# multiply each per game stat by that season's weight
rb_stats = rb_stats.with_columns(
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

    weighted_carries_per_game=(
        pl.col("carries_per_game") * pl.col("season_weight")
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
# collapse the three seasons back into one row per RB by adding each weighted per games together
rb_weighted_stats = rb_stats.group_by("player_id").agg(
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

    pl.col("weighted_carries_per_game")
        .sum()
        .alias("carries_per_game"),

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

# join the weighted stats back to rbs
rb_player_data = rbs.join(
    rb_weighted_stats,
    left_on="gsis_id",
    right_on="player_id",
    how="left"
)

# convert birth_date string into actual dates
rb_player_data = rb_player_data.with_columns(
    pl.col("birth_date")
    .str.to_date("%Y-%m-%d", strict=False)
    .alias("birth_date")
)

# calculate age using map_elements
rb_player_data = rb_player_data.with_columns(
    age=pl.col("birth_date").map_elements(
        calculate_age,
        return_dtype=pl.Float64
    )
)

# select only what is needed for the RB model
rb_player_data = rb_player_data.select([
    pl.col("gsis_id"),
    pl.col("display_name").alias("name"),
    pl.col("position"),
    pl.col("latest_team").alias("team"),
    pl.col("age"),

    pl.col("receptions_per_game"),
    pl.col("targets_per_game"),
    pl.col("receiving_yards_per_game"),
    pl.col("receiving_tds_per_game"),
    pl.col("carries_per_game"),
    pl.col("rushing_yards_per_game"),
    pl.col("rushing_tds_per_game"),
    pl.col("points_per_game")
])

# add dynasty market value
rb_player_data = rb_player_data.with_columns(
    market_value=pl.col("name").map_elements(
        lambda name: rb_market.get(name, 0),
        return_dtype=pl.Int64
    )
)

# fill any null columns with 0
rb_player_data = rb_player_data.fill_null(0)

# save into a separate rb player data csv
rb_player_data.write_csv("rb_player_data.csv")

# TIGHT ENDS
# TE-only tables
tes = fantasy_players.filter(
    pl.col("position") == "TE"
)

te_stats = stats.filter(
    pl.col("position") == "TE"
)

# attach the rookie season of the te so we know which seasons should count
te_stats = te_stats.join(tes.select(
    ["gsis_id", "rookie_season"]),
        left_on = "player_id",
        right_on="gsis_id",
        how="inner"
)

# calculate the per-game values for every season separately
te_stats = te_stats.with_columns(
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
te_stats = te_stats.with_columns(
    season_weight=pl.struct(
        ["season", "rookie_season"]
    ).map_elements(
        lambda row: calculate_season_weight(
            row["season"],
            row["rookie_season"],
            SEASON_WEIGHTS
        ),
        return_dtype=pl.Float64
    )
)

# multiply each per game stat by that season's weight
te_stats = te_stats.with_columns(
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
# collapse the three seasons back into one row per TE by adding each weighted per games together
te_weighted_stats = te_stats.group_by("player_id").agg(
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
                
# join the weighted stats back to tes
te_player_data = tes.join(
    te_weighted_stats,
    left_on="gsis_id",
    right_on="player_id",
    how="left"
)

# convert birth_date string into actual dates
te_player_data = te_player_data.with_columns(
    pl.col("birth_date")
    .str.to_date("%Y-%m-%d", strict=False)
    .alias("birth_date")
)

# calculate age using map_elements
te_player_data = te_player_data.with_columns(
    age=pl.col("birth_date").map_elements(
        calculate_age,
        return_dtype=pl.Float64
    )
)

# select only what is needed for the TE model
te_player_data = te_player_data.select([
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

# add dynasty market value
te_player_data = te_player_data.with_columns(
    market_value=pl.col("name").map_elements(
        lambda name: te_market.get(name, 0),
        return_dtype=pl.Int64
    )
)

# fill any null columns with 0
te_player_data = te_player_data.fill_null(0)

# save into a separate te player data csv
te_player_data.write_csv("te_player_data.csv")


# QUARTER BACKS
# QB-only tables
qbs = fantasy_players.filter(
    pl.col("position") == "QB"
)

qb_stats = stats.filter(
    pl.col("position") == "QB"
)

# attach the rookie season of the qb so we know which seasons should count
qb_stats = qb_stats.join(qbs.select(
    ["gsis_id", "rookie_season"]),
        left_on="player_id",
        right_on="gsis_id",
        how="inner"
)

# calculate the per-game values for every season separately
qb_stats = qb_stats.with_columns(
    completions_per_game=pl.struct(
        ["completions", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["completions"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    attempts_per_game=pl.struct(
        ["attempts", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["attempts"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    passing_yards_per_game=pl.struct(
        ["passing_yards", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["passing_yards"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    passing_tds_per_game=pl.struct(
        ["passing_tds", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["passing_tds"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    interceptions_per_game=pl.struct(
        ["passing_interceptions", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["passing_interceptions"],
            row["games"]
        ),
        return_dtype=pl.Float64
    ),

    carries_per_game=pl.struct(
        ["carries", "games"]
    ).map_elements(
        lambda row: calculate_per_game(
            row["carries"],
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
qb_stats = qb_stats.with_columns(
    season_weight=pl.struct(
        ["season", "rookie_season"]
    ).map_elements(
        lambda row: calculate_season_weight(
            row["season"],
            row["rookie_season"],
            SEASON_WEIGHTS
        ),
        return_dtype=pl.Float64
    )
)

# multiply each per game stat by that season's weight
qb_stats = qb_stats.with_columns(
    weighted_completions_per_game=(
        pl.col("completions_per_game") * pl.col("season_weight")
    ),

    weighted_attempts_per_game=(
        pl.col("attempts_per_game") * pl.col("season_weight")
    ),

    weighted_passing_yards_per_game=(
        pl.col("passing_yards_per_game") * pl.col("season_weight")
    ),

    weighted_passing_tds_per_game=(
        pl.col("passing_tds_per_game") * pl.col("season_weight")
    ),

    weighted_interceptions_per_game=(
        pl.col("interceptions_per_game") * pl.col("season_weight")
    ),

    weighted_carries_per_game=(
        pl.col("carries_per_game") * pl.col("season_weight")
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
# collapse the three seasons back into one row per QB by adding each weighted per games together
qb_weighted_stats = qb_stats.group_by("player_id").agg(
    pl.col("weighted_completions_per_game")
        .sum()
        .alias("completions_per_game"),

    pl.col("weighted_attempts_per_game")
        .sum()
        .alias("attempts_per_game"),

    pl.col("weighted_passing_yards_per_game")
        .sum()
        .alias("passing_yards_per_game"),

    pl.col("weighted_passing_tds_per_game")
        .sum()
        .alias("passing_tds_per_game"),

    pl.col("weighted_interceptions_per_game")
        .sum()
        .alias("interceptions_per_game"),

    pl.col("weighted_carries_per_game")
        .sum()
        .alias("carries_per_game"),

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

# join the weighted stats back to qbs
qb_player_data = qbs.join(
    qb_weighted_stats,
    left_on="gsis_id",
    right_on="player_id",
    how="left"
)

# convert birth_date string into actual dates
qb_player_data = qb_player_data.with_columns(
    pl.col("birth_date")
    .str.to_date("%Y-%m-%d", strict=False)
    .alias("birth_date")
)

# calculate age using map_elements
qb_player_data = qb_player_data.with_columns(
    age=pl.col("birth_date").map_elements(
        calculate_age,
        return_dtype=pl.Float64
    )
)

# select only what is needed for the QB model
qb_player_data = qb_player_data.select([
    pl.col("gsis_id"),
    pl.col("display_name").alias("name"),
    pl.col("position"),
    pl.col("latest_team").alias("team"),
    pl.col("age"),

    pl.col("completions_per_game"),
    pl.col("attempts_per_game"),
    pl.col("passing_yards_per_game"),
    pl.col("passing_tds_per_game"),
    pl.col("interceptions_per_game"),
    pl.col("carries_per_game"),
    pl.col("rushing_yards_per_game"),
    pl.col("rushing_tds_per_game"),
    pl.col("points_per_game")
])

# add dynasty market value
qb_player_data = qb_player_data.with_columns(
    market_value=pl.col("name").map_elements(
        lambda name: qb_market.get(name, 0),
        return_dtype=pl.Int64
    )
)

# fill any null columns with 0
qb_player_data = qb_player_data.fill_null(0)

# save into a separate qb player data csv
qb_player_data.write_csv("qb_player_data.csv")

# # save the data to the csv
# player_data.write_csv("player_data.csv")