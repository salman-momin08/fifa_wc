from typing import Dict, Any, List

class SustainabilityService:
    @staticmethod
    def get_refill_and_recycle_stations(gate: str) -> Dict[str, Any]:
        # Mock mapping of stations based on location
        refill_stations = {
            "Gate A": "Concourse North Refill (50m)",
            "Gate B": "Concourse East Refill (40m)",
            "Gate C": "South Outer Ring Hub (80m)",
            "Transit Plaza": "Plaza Central Station (20m)",
            "Concourse West": "West Wing refill fountain (10m)",
            "Concourse East": "East Wing refill fountain (15m)",
            "South Stand": "South Plaza Hub (60m)"
        }
        recycling_bins = {
            "Gate A": "Gate A Green Waste Cans",
            "Gate B": "Gate B Recycling Pod 4",
            "Gate C": "Concourse East Green Bin Hub",
            "Transit Plaza": "Bus Station Smart Bins",
            "Concourse West": "Concourse West Smart Bins",
            "Concourse East": "Concourse East Smart Bins",
            "South Stand": "Grandstand Recycling Hub"
        }
        ev_shuttles = {
            "Gate A": "Shuttle Hub North (100m)",
            "Gate B": "Shuttle Hub East (150m)",
            "Gate C": "South Transit Ring (120m)",
            "Transit Plaza": "Plaza Express Terminal (30m)",
            "Concourse West": "West Terminal (200m)",
            "Concourse East": "East Terminal (180m)",
            "South Stand": "South Outer Hub (250m)"
        }
        
        return {
            "nearest_refill": refill_stations.get(gate, "Concourse Main Ring Refill"),
            "nearest_recycle": recycling_bins.get(gate, "General Waste Bins"),
            "nearest_ev_shuttle": ev_shuttles.get(gate, "Plaza Transit Hub")
        }

    @classmethod
    def calculate_green_impact(cls, user_refills: int, public_trans_used: bool) -> Dict[str, Any]:
        # 1 refill saves 1 single-use plastic bottle (~25 grams of plastic)
        plastic_saved_grams = user_refills * 25.0
        
        # Public transit reduces CO2 by ~2.6 kg per passenger trip vs driving
        co2_reduction_kg = 2.6 if public_trans_used else 0.0
        co2_reduction_kg += (user_refills * 0.08)  # Plastic manufacturing savings (~80g per bottle)

        # Gamified Green Score calculation
        green_score = (user_refills * 10) + (100 if public_trans_used else 0)

        # Rank definition
        rank = "Green Fan Starter"
        if green_score >= 150:
            rank = "Eco Tournament Legend"
        elif green_score >= 80:
            rank = "Stadium Planet Champion"
        elif green_score >= 30:
            rank = "Active Eco Spectator"

        return {
            "plastic_saved_grams": round(plastic_saved_grams, 1),
            "co2_reduction_kg": round(co2_reduction_kg, 2),
            "green_score": green_score,
            "eco_rank": rank,
            "gamification_badges": cls.get_badges(green_score, user_refills)
        }

    @staticmethod
    def get_badges(score: int, refills: int) -> List[str]:
        badges = []
        if refills > 0:
            badges.append("Hydration Hero")
        if refills >= 5:
            badges.append("Zero Waste Advocate")
        if score >= 100:
            badges.append("Green Transport Pioneer")
        if score >= 150:
            badges.append("Eco MVP")
        return badges
