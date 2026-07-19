"""
Accessible Dijkstra Route Optimization Engine.

Computes weighted multi-criteria shortest paths across stadium graph nodes,
incorporating step-free accessibility constraints, real-time crowd density penalties,
transit delay bulletins, and fan preference profiles (fastest, safest, least_crowded, accessible).
"""
import heapq
from typing import Any, Dict, List, Optional, Tuple

from app.database import CrowdSensor, TransitAlert, WayfindingNode
from app.repositories.stadium import StadiumRepository

# Adjacency list representation of stadium paths:
# Each node maps to its neighbors with distance (meters) and transport type (walking, shuttle, bus, metro)
STADIUM_GRAPH: Dict[str, List[Tuple[str, float, str]]] = {
    "Transit Plaza": [
        ("Gate A", 300, "walking"),
        ("Gate B", 400, "walking"),
        ("Concourse East", 500, "walking"),
        ("Concourse West", 600, "walking"),
        ("South Stand", 200, "walking"),
    ],
    "Gate A": [
        ("Transit Plaza", 300, "walking"),
        ("Concourse West", 200, "walking"),
        ("Gate B", 350, "shuttle"),
    ],
    "Gate B": [
        ("Transit Plaza", 400, "walking"),
        ("Gate A", 350, "shuttle"),
        ("Concourse East", 250, "walking"),
    ],
    "Gate C": [
        ("Concourse West", 300, "walking"),
        ("Concourse East", 300, "walking"),
    ],
    "Concourse West": [
        ("Transit Plaza", 600, "walking"),
        ("Gate A", 200, "walking"),
        ("Gate C", 300, "walking"),
        ("South Stand", 400, "walking"),
    ],
    "Concourse East": [
        ("Transit Plaza", 500, "walking"),
        ("Gate B", 250, "walking"),
        ("Gate C", 300, "walking"),
    ],
    "South Stand": [
        ("Transit Plaza", 200, "walking"),
        ("Concourse West", 400, "walking"),
    ],
}


class RouteOptimizer:
    """Service class providing multi-criteria Dijkstra route optimization."""

    @staticmethod
    def calculate_cost(
        distance: float,
        mode: str,
        transit_alerts: Dict[str, TransitAlert],
        crowd_sensors: Dict[str, CrowdSensor],
        preference: str,
        accessible: bool,
        target_node_obj: Optional[WayfindingNode],
    ) -> float:
        """Calculate dynamic edge cost for Dijkstra pathfinding.

        Args:
            distance: Edge length in meters.
            mode: Transport mode ('walking', 'shuttle', 'bus', 'metro').
            transit_alerts: Map of active route alerts.
            crowd_sensors: Map of zone crowd density sensors.
            preference: Fan routing preference ('fastest', 'safest', 'least_crowded').
            accessible: True to require step-free wheelchair ramp / elevator access.
            target_node_obj: Destination WayfindingNode instance.

        Returns:
            Computed edge cost value or float('inf') if path is invalid/inaccessible.
        """
        # 1. Accessibility constraint
        if accessible and target_node_obj:
            if not (target_node_obj.has_wheelchair_ramp or target_node_obj.has_elevator):
                return float("inf")

        # 2. Base walking speed (~80m/min) vs shuttle speed (~300m/min)
        base_speed = 300.0 if mode == "shuttle" else 80.0
        base_time = distance / base_speed

        # 3. Add transit delay penalty
        if mode == "shuttle" and "Shuttle Route 101" in transit_alerts:
            alert = transit_alerts["Shuttle Route 101"]
            if alert.status == "delayed":
                base_time += alert.delay_minutes

        # 4. Crowd density penalty
        if target_node_obj and target_node_obj.zone in crowd_sensors:
            sensor = crowd_sensors[target_node_obj.zone]
            if sensor.density_percentage > 80:
                base_time *= 1.8
            elif sensor.density_percentage > 50:
                base_time *= 1.3

        # 5. Apply preference multipliers
        if preference == "fastest":
            return base_time
        elif preference == "least_crowded" and target_node_obj and target_node_obj.name in crowd_sensors:
            density = crowd_sensors[target_node_obj.name].density_percentage
            return base_time + (density * 5.0)
        elif preference == "safest":
            density_val = (
                crowd_sensors[target_node_obj.name].density_percentage
                if target_node_obj and target_node_obj.name in crowd_sensors
                else 0
            )
            if density_val > 80:
                return base_time + 1000.0
            return base_time

        return base_time

    @classmethod
    def find_route(
        cls,
        nodes_list: List[WayfindingNode],
        transit_alerts_list: List[TransitAlert],
        crowd_sensors_list: List[CrowdSensor],
        start: str,
        end: str,
        preference: str = "fastest",
        accessible: bool = False,
    ) -> Dict[str, Any]:
        """Compute Dijkstra path given pre-fetched list collections.

        Args:
            nodes_list: List of WayfindingNode records from DB.
            transit_alerts_list: List of TransitAlert records.
            crowd_sensors_list: List of CrowdSensor records.
            start: Starting waypoint name.
            end: Target destination waypoint name.
            preference: Routing preference profile.
            accessible: Step-free access requirement flag.

        Returns:
            Dictionary with path, modes, eta_minutes, preference, accessible, and verified status.
        """
        nodes_map = {n.name: n for n in nodes_list}
        alerts_map = {a.route: a for a in transit_alerts_list}
        sensors_map = {c.zone: c for c in crowd_sensors_list}

        if start not in STADIUM_GRAPH or end not in STADIUM_GRAPH:
            return {"error": "Invalid start or destination point"}

        queue: List[Tuple[float, str, List[str], List[str]]] = [(0.0, start, [start], [])]
        visited = set()

        best_cost = float("inf")
        best_path: List[str] = []
        best_modes: List[str] = []

        while queue:
            cost, current, path, modes = heapq.heappop(queue)

            if current == end:
                if cost < best_cost:
                    best_cost = cost
                    best_path = path
                    best_modes = modes
                break

            if current in visited:
                continue
            visited.add(current)

            for neighbor, dist, transport_mode in STADIUM_GRAPH.get(current, []):
                if neighbor in visited:
                    continue

                neighbor_obj = nodes_map.get(neighbor)
                edge_cost = cls.calculate_cost(
                    dist, transport_mode, alerts_map, sensors_map, preference, accessible, neighbor_obj
                )

                if edge_cost == float("inf"):
                    continue

                heapq.heappush(queue, (cost + edge_cost, neighbor, path + [neighbor], modes + [transport_mode]))

        if best_cost == float("inf") or not best_path:
            return {
                "route": [start, end],
                "path": [start, end],
                "modes": ["walking"],
                "eta_minutes": 15.0,
                "preference": preference,
                "accessible": accessible,
                "verified": False,
                "success": False,
                "note": "Offline direct corridor routing active.",
            }

        return {
            "route": best_path,
            "path": best_path,
            "modes": best_modes,
            "eta_minutes": round(best_cost, 1),
            "preference": preference,
            "accessible": accessible,
            "verified": True,
            "success": True,
        }

    @classmethod
    def find_optimal_route(
        cls,
        db_session: Any,
        start_node_name: str,
        target_node_name: str,
        preference: str = "fastest",
        accessible: bool = False,
    ) -> Dict[str, Any]:
        """Database-backed routing method alias used by test suite and service callers.

        Args:
            db_session: SQLAlchemy Session instance.
            start_node_name: Name of origin waypoint.
            target_node_name: Name of destination waypoint.
            preference: Preferred routing strategy.
            accessible: Step-free access requirement flag.

        Returns:
            Dictionary containing computed path, success flag, and eta_minutes.
        """
        repo = StadiumRepository(db_session)
        nodes = repo.get_wayfinding_nodes()
        alerts = repo.get_transit_alerts()
        sensors = repo.get_crowd_sensors()
        return cls.find_route(nodes, alerts, sensors, start_node_name, target_node_name, preference, accessible)
