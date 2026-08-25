import nflreadpy as nfl

players = nfl.load_players()

# using polars to filter for only the 4 relevant fantasy positions and make sure they are still active
fantasy_players = players.filter(players["position"].is_in(["QB", "RB", "WR", "TE"]) & (players["last_season"] == 2026))

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

print(fantasy_players.shape)

print(
    fantasy_players
    .group_by("status")
    .len()
    .sort("len", descending=True)
)

print(
    fantasy_players.filter(
        fantasy_players["status"] == "RLS"
    )
)