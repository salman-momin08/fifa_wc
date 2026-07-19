from typing import Dict, Any

class CrowdAnalyticsService:
    @staticmethod
    def predict_density(
        current_density: int,
        entry_rate_per_min: float = 12.0,
        exit_rate_per_min: float = 8.0,
        has_match_ending_soon: bool = False
    ) -> Dict[str, Any]:
        # Net flow coefficient
        net_flow = entry_rate_per_min - exit_rate_per_min
        
        # If match is ending, outflow surges
        if has_match_ending_soon:
            net_flow -= 25.0  # Heavy outbound flow

        # Projections with 0-100 boundary clamps
        pred_15 = max(0, min(100, int(current_density + (net_flow * 15 * 0.15))))
        pred_30 = max(0, min(100, int(current_density + (net_flow * 30 * 0.15))))
        pred_60 = max(0, min(100, int(current_density + (net_flow * 60 * 0.15))))

        # Explainable recommendation logic
        recommendation = "Flow density remains stable. Continue regular monitoring."
        alert_level = "low"
        
        if pred_15 >= 85 or pred_30 >= 90:
            recommendation = (
                f"Critical congestion forecast ({pred_30}% in 30m). "
                "ACTION: Activate secondary gates, trigger spectator redirection alerts, "
                "and deploy crowd control staff to outer loops."
            )
            alert_level = "high"
        elif pred_30 > 70 or pred_60 > 80:
            recommendation = (
                f"Moderate congestion predicted ({pred_30}% in 30m). "
                "ACTION: Notify ground staff to prepare dynamic queues and stand-by corridors."
            )
            alert_level = "medium"
        elif pred_60 < 30 and net_flow < 0:
            recommendation = "Zone clearing. Prepare to transition checkpoints to standby mode."
            alert_level = "low"

        return {
            "current_density": current_density,
            "predictions": {
                "in_15_mins": pred_15,
                "in_30_mins": pred_30,
                "in_60_mins": pred_60
            },
            "recommendation": recommendation,
            "alert_level": alert_level
        }
