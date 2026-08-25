from datetime import date

def calculate_age(birth_date: date) -> float:
    """Calculate a player's current age from their birthdate"""
    today = date.today()

    days_alive = (today - birth_date).days

    return round(days_alive / 365.2425, 2)

def calculate_per_game(stat: float | None, games: int | None) -> float:
    """Calculate a statistic on a per game basis"""
    if stat is None or games is None or games <= 0:
        return 0.0

    return round(stat / games, 2)

def calculate_season_weight(season: int, rookie_season: int, season_weights: dict[int, float]) -> float:
    """Calculate a normalized weight for a player's available seasons."""
    # dictionary of valid weights
    available_weights = {}

    for year, weight in season_weights.items():
        if year >= rookie_season:   # we have to make sure the only seasons that count are ones where the WR was actually in the NFL
            available_weights[year] = weight

    total_weight = sum(available_weights.values())

    if season not in available_weights or total_weight == 0:
        return 0.0

    # Take the season weight and divide it by the total weight to get the actual weight of the season.
    # This way a players weight will always add up to 1 regardless of how many seasons they've played in the NFL
    return season_weights[season] / total_weight    