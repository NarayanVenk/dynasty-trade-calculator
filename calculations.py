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

def calculate_wr_age_score(age: float) -> float:
    """Calculate dynasty age value for wide receivers."""
    if age <= 23:
        return 70

    elif age <= 25:
        return 70 - (age - 23) * 5

    elif age <= 27:
        return 60 - (age - 25) * 5

    elif age <= 29:
        return 50 - (age - 27) * 10

    elif age <= 31:
        return 30 - (age - 29) * 15

    else:
        return 0 - (age - 31) * 20

def calculate_rb_age_score(age: float) -> float:
    """Calculate dynasty age value for running backs."""
    if age <= 23:
        return 70

    elif age <= 25:
        return 70 - (age - 23) * 10

    elif age <= 27:
        return 60 - (age - 25) * 10

    elif age <= 29:
        return 50 - (age - 27) * 15

    elif age <= 31:
        return 30 - (age - 29) * 20

    else:
        return 0 - (age - 31) * 25

def calculate_te_age_score(age: float) -> float:
    """Calculate dynasty age value for tight ends."""
    if age <= 23:
        return 70

    elif age <= 25:
        return 70 - (age - 23) * 5

    elif age <= 27:
        return 60 - (age - 25) * 5

    elif age <= 29:
        return 50 - (age - 27) * 10

    elif age <= 31:
        return 30 - (age - 29) * 15

    else:
        return 0 - (age - 31) * 20

def calculate_market_value(market_value: float | None) -> float:
    """Calculate dynasty market value for the player to use in the value model."""
    if market_value is None or market_value <= 0:
        return 0.0

    # this formula is so that the value matters but does not completely erase the statistical model
    return round(market_value / 20, 2)

def normalize_player_name(name: str) -> str:
    """Normalize player names so names from different data sources can match."""
    suffixes = [" Jr.", " Sr.", " II", " III", " IV"]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()

    return name