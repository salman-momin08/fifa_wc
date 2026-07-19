"""
Sustainability & Gamification Service.

Provides location-aware eco nudge lookups, plastic/CO2 impact calculators,
green score computation, and gamification badge unlocking for the FIFA WC 2026
Green Initiative programme.
"""
from typing import Dict, Any, List


# Sustainability impact constants
PLASTIC_PER_REFILL_GRAMS: float = 25.0
CO2_PER_TRANSIT_TRIP_KG: float = 2.6
CO2_PER_BOTTLE_AVOIDED_KG: float = 0.08
GREEN_SCORE_PER_REFILL: int = 10
GREEN_SCORE_PER_TRANSIT: int = 100


class SustainabilityService:
    """Service class for environmental impact tracking and fan gamification."""

    # Station lookup maps (anchored to wayfinding_nodes zone names)
    _REFILL_STATIONS: Dict[str, str] = {
        "Gate A": "Concourse North Refill (50m)",
        "Gate B": "Concourse East Refill (40m)",
        "Gate C": "South Outer Ring Hub (80m)",
        "Transit Plaza": "Plaza Central Station (20m)",
        "Concourse West": "West Wing refill fountain (10m)",
        "Concourse East": "East Wing refill fountain (15m)",
        "South Stand": "South Plaza Hub (60m)",
    }
    _RECYCLING_BINS: Dict[str, str] = {
        "Gate A": "Gate A Green Waste Cans",
        "Gate B": "Gate B Recycling Pod 4",
        "Gate C": "Concourse East Green Bin Hub",
        "Transit Plaza": "Bus Station Smart Bins",
        "Concourse West": "Concourse West Smart Bins",
        "Concourse East": "Concourse East Smart Bins",
        "South Stand": "Grandstand Recycling Hub",
    }
    _EV_SHUTTLES: Dict[str, str] = {
        "Gate A": "Shuttle Hub North (100m)",
        "Gate B": "Shuttle Hub East (150m)",
        "Gate C": "South Transit Ring (120m)",
        "Transit Plaza": "Plaza Express Terminal (30m)",
        "Concourse West": "West Terminal (200m)",
        "Concourse East": "East Terminal (180m)",
        "South Stand": "South Outer Hub (250m)",
    }

    @classmethod
    def get_refill_and_recycle_stations(cls, gate: str) -> Dict[str, str]:
        """Return nearest refill, recycling, and EV shuttle locations for a given gate.

        Args:
            gate: Gate or zone name matching a wayfinding_node name.

        Returns:
            Dictionary with nearest_refill, nearest_recycle, and nearest_ev_shuttle keys.
        """
        return {
            "nearest_refill": cls._REFILL_STATIONS.get(gate, "Concourse Main Ring Refill"),
            "nearest_recycle": cls._RECYCLING_BINS.get(gate, "General Waste Bins"),
            "nearest_ev_shuttle": cls._EV_SHUTTLES.get(gate, "Plaza Transit Hub"),
        }

    @classmethod
    def calculate_green_impact(cls, user_refills: int, public_trans_used: bool) -> Dict[str, Any]:
        """Calculate sustainability impact from fan eco-actions.

        Args:
            user_refills: Number of water bottle refills the fan has recorded.
            public_trans_used: True if fan arrived via public transit.

        Returns:
            Dictionary with plastic_saved_grams, co2_reduction_kg, green_score, eco_rank, badges.
        """
        plastic_saved_grams = user_refills * PLASTIC_PER_REFILL_GRAMS
        co2_reduction_kg = (CO2_PER_TRANSIT_TRIP_KG if public_trans_used else 0.0) + (
            user_refills * CO2_PER_BOTTLE_AVOIDED_KG
        )
        green_score = (user_refills * GREEN_SCORE_PER_REFILL) + (
            GREEN_SCORE_PER_TRANSIT if public_trans_used else 0
        )

        rank = cls._compute_rank(green_score)
        return {
            "plastic_saved_grams": round(plastic_saved_grams, 1),
            "co2_reduction_kg": round(co2_reduction_kg, 2),
            "green_score": green_score,
            "eco_rank": rank,
            "gamification_badges": cls.get_badges(green_score, user_refills),
        }

    @classmethod
    def calculate_impact(cls, refill_actions: int, transit_trips: int) -> Dict[str, Any]:
        """Calculate sustainability impact using named action parameters.

        Convenience alias used by the test suite with explicit keyword arguments.

        Args:
            refill_actions: Number of water bottle refill actions recorded.
            transit_trips: Number of public transit trips taken (0 or 1+).

        Returns:
            Dictionary with plastic_saved_grams, co2_reduced_grams, badge, green_score, eco_rank.
        """
        plastic_saved_grams = refill_actions * PLASTIC_PER_REFILL_GRAMS
        co2_reduced_grams = (
            (CO2_PER_TRANSIT_TRIP_KG * transit_trips * 1000)
            + (refill_actions * CO2_PER_BOTTLE_AVOIDED_KG * 1000)
        )
        green_score = (refill_actions * GREEN_SCORE_PER_REFILL) + (transit_trips * GREEN_SCORE_PER_TRANSIT)
        badges = cls.get_badges(green_score, refill_actions)

        return {
            "plastic_saved_grams": round(plastic_saved_grams, 1),
            "co2_reduced_grams": round(co2_reduced_grams, 1),
            "green_score": green_score,
            "eco_rank": cls._compute_rank(green_score),
            "badge": badges[0] if badges else "Eco Starter",
            "gamification_badges": badges,
        }

    @staticmethod
    def _compute_rank(green_score: int) -> str:
        """Determine eco rank label from green score.

        Args:
            green_score: Integer composite green score value.

        Returns:
            Human-readable rank string.
        """
        if green_score >= 150:
            return "Eco Tournament Legend"
        if green_score >= 80:
            return "Stadium Planet Champion"
        if green_score >= 30:
            return "Active Eco Spectator"
        return "Green Fan Starter"

    @staticmethod
    def get_badges(score: int, refills: int) -> List[str]:
        """Return list of earned gamification badge names.

        Args:
            score: Cumulative green score.
            refills: Number of refill actions for badge threshold checks.

        Returns:
            List of badge name strings earned by the fan.
        """
        badges: List[str] = []
        if refills > 0:
            badges.append("Hydration Hero")
        if refills >= 5:
            badges.append("Zero Waste Advocate")
        if score >= 100:
            badges.append("Green Transport Pioneer")
        if score >= 150:
            badges.append("Eco MVP")
        return badges
