from datetime import date

def calculate_age(birth_date: date) -> float:
    """Calculate a player's current age from their birthdate"""
    today = date.today()

    days_alive = (today - birth_date).days

    return round(days_alive / 365.2425, 2)

def calculate_points_per_game(fantasy_points: float | None, games: int | None) -> float:
    """Calculate fantasy points per game"""
    if fantasy_points is None or games is None or games <= 0:
        return 0.0

    return round(fantasy_points / games, 2)