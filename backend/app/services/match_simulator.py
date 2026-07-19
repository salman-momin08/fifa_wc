import time
import random
from typing import Dict, Any

class MatchSimulator:
    """
    Dynamic Match Telemetry Engine.
    Simulates live FIFA World Cup match statistics (match minutes ticking,
    possession fluctuations, shots on goal, pass accuracy, and stadium capacity)
    in real-time based on system clock elapsed intervals.
    """
    @staticmethod
    def get_dynamic_telemetry(db_match) -> Dict[str, Any]:
        current_time = time.time()
        
        # Calculate dynamic match minute (0 to 90+ minutes cycling smoothly over real time)
        elapsed_mins = int((current_time % 5400) / 60)
        if elapsed_mins == 0:
            elapsed_mins = 1

        if elapsed_mins > 90:
            minute_str = f"90+{elapsed_mins - 90}'"
        else:
            minute_str = f"{elapsed_mins}'"

        # Seed pseudo-random generator with 5-second interval timestamp so state is synchronized across all clients
        seed = int(current_time / 5)
        rng = random.Random(seed)

        # Dynamic statistical fluctuations
        possession_home = max(40, min(65, 52 + rng.randint(-3, 3)))
        possession_away = 100 - possession_home

        shots_home = min(22, max(2, int(elapsed_mins / 5) + rng.randint(0, 2)))
        shots_away = min(18, max(1, int(elapsed_mins / 7) + rng.randint(0, 2)))

        pass_acc_home = max(75, min(94, 85 + rng.randint(-2, 2)))
        pass_acc_away = max(70, min(90, 81 + rng.randint(-2, 2)))

        capacity_pct = round(min(98.5, max(85.0, 92.4 + (rng.randint(-8, 8) / 10.0))), 1)
        attendance_num = int(68243 + (capacity_pct - 92.4) * 500)

        # Allow DB score overrides if set by match API update
        home_score = db_match.home_score if db_match and db_match.home_score is not None else (1 if elapsed_mins > 30 else 0)
        away_score = db_match.away_score if db_match and db_match.away_score is not None else (1 if elapsed_mins > 60 else 0)

        home_team = db_match.home_team if db_match else "CANADA"
        home_flag = db_match.home_flag if db_match else "🇨🇦"
        away_team = db_match.away_team if db_match else "USA"
        away_flag = db_match.away_flag if db_match else "🇺🇸"

        return {
            "id": db_match.id if db_match else 1,
            "home_team": home_team,
            "home_flag": home_flag,
            "home_score": home_score,
            "away_team": away_team,
            "away_flag": away_flag,
            "away_score": away_score,
            "match_minute": minute_str,
            "is_live": elapsed_mins <= 90,
            "possession_home": possession_home,
            "possession_away": possession_away,
            "shots_home": shots_home,
            "shots_away": shots_away,
            "pass_accuracy_home": pass_acc_home,
            "pass_accuracy_away": pass_acc_away,
            "attendance": f"{attendance_num:,}",
            "stadium_capacity_pct": capacity_pct
        }
