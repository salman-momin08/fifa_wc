"""
Crowd Predictive Analytics Service.

Applies a differential flow model to project future crowd density levels
at 15-minute, 30-minute, and 60-minute intervals. Generates tiered advisory
notifications with explainable reasoning for stadium coordinators.
"""
from typing import Dict, Any

from app.core.constants import (
    CROWD_CRITICAL_FORECAST_THRESHOLD,
    CROWD_HIGH_DENSITY_THRESHOLD,
)


class CrowdAnalyticsService:
    """Service class for real-time crowd density prediction and advisory generation."""

    # Default flow coefficients (fans per minute)
    DEFAULT_ENTRY_RATE: float = 12.0
    DEFAULT_EXIT_RATE: float = 8.0
    FLOW_TIME_COEFFICIENT: float = 0.15
    MATCH_END_SURGE: float = 25.0

    @classmethod
    def predict_density(
        cls,
        current_density: int,
        entry_rate_per_min: float = 12.0,
        exit_rate_per_min: float = 8.0,
        has_match_ending_soon: bool = False,
    ) -> Dict[str, Any]:
        """Compute predictive density forecast using differential flow model.

        Args:
            current_density: Current zone density percentage (0-100).
            entry_rate_per_min: Estimated fan entry rate per minute.
            exit_rate_per_min: Estimated fan exit rate per minute.
            has_match_ending_soon: Applies surge exit coefficient when True.

        Returns:
            Dictionary with predictions at 15m/30m/60m, recommendation, and alert_level.
        """
        return cls._compute_forecast(
            current_density, entry_rate_per_min, exit_rate_per_min, has_match_ending_soon
        )

    @classmethod
    def predict_density_trend(
        cls,
        current_density: int,
        entry_rate_per_min: float = 12.0,
        exit_rate_per_min: float = 8.0,
        has_match_ending_soon: bool = False,
    ) -> Dict[str, Any]:
        """Alias for predict_density that returns individual forecast keys.

        Returns a flat dictionary with ``forecast_15m``, ``forecast_30m``,
        ``forecast_60m`` keys for test-friendly access.

        Args:
            current_density: Current zone density percentage (0-100).
            entry_rate_per_min: Estimated fan entry rate per minute.
            exit_rate_per_min: Estimated fan exit rate per minute.
            has_match_ending_soon: Applies surge exit coefficient when True.

        Returns:
            Flat dictionary with forecast_15m, forecast_30m, forecast_60m, recommendation.
        """
        result = cls._compute_forecast(
            current_density, entry_rate_per_min, exit_rate_per_min, has_match_ending_soon
        )
        predictions = result["predictions"]
        return {
            "forecast_15m": predictions["in_15_mins"],
            "forecast_30m": predictions["in_30_mins"],
            "forecast_60m": predictions["in_60_mins"],
            "current_density": result["current_density"],
            "recommendation": result["recommendation"],
            "alert_level": result["alert_level"],
        }

    @classmethod
    def _compute_forecast(
        cls,
        current_density: int,
        entry_rate_per_min: float,
        exit_rate_per_min: float,
        has_match_ending_soon: bool,
    ) -> Dict[str, Any]:
        """Internal forecast computation shared by predict_density and predict_density_trend.

        Args:
            current_density: Current zone density percentage (0-100).
            entry_rate_per_min: Estimated fan entry rate per minute.
            exit_rate_per_min: Estimated fan exit rate per minute.
            has_match_ending_soon: Applies surge exit coefficient when True.

        Returns:
            Standardized forecast dictionary.
        """
        net_flow = entry_rate_per_min - exit_rate_per_min

        # If match is ending, outflow surges dramatically
        if has_match_ending_soon:
            net_flow -= cls.MATCH_END_SURGE

        # Projections clamped to valid 0-100 range
        pred_15 = max(0, min(100, int(current_density + (net_flow * 15 * cls.FLOW_TIME_COEFFICIENT))))
        pred_30 = max(0, min(100, int(current_density + (net_flow * 30 * cls.FLOW_TIME_COEFFICIENT))))
        pred_60 = max(0, min(100, int(current_density + (net_flow * 60 * cls.FLOW_TIME_COEFFICIENT))))

        recommendation = "Flow density remains stable. Continue regular monitoring."
        alert_level = "low"

        if pred_15 >= CROWD_CRITICAL_FORECAST_THRESHOLD or pred_30 >= 90:
            recommendation = (
                f"Critical congestion forecast ({pred_30}% in 30m). "
                "ACTION: Activate secondary gates, trigger spectator redirection alerts, "
                "and deploy crowd control staff to outer loops."
            )
            alert_level = "high"
        elif pred_30 > CROWD_HIGH_DENSITY_THRESHOLD or pred_60 > 80:
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
                "in_60_mins": pred_60,
            },
            "recommendation": recommendation,
            "alert_level": alert_level,
        }
