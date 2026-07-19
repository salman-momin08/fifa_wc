from typing import List, Dict, Any, Tuple
import heapq
from app.database import WayfindingNode, TransitAlert, CrowdSensor

# Adjacency list representation of stadium paths:
# Each node maps to its neighbors with distance (meters) and transport type (walking, shuttle, bus, metro)
STADIUM_GRAPH = {
    "Transit Plaza": [
        ("Gate A", 300, "walking"),
        ("Gate B", 400, "walking"),
        ("Concourse East", 500, "walking"),
        ("Concourse West", 600, "walking"),
        ("South Stand", 200, "walking")
    ],
    "Gate A": [
        ("Transit Plaza", 300, "walking"),
        ("Concourse West", 200, "walking"),
        ("Gate B", 350, "shuttle")
    ],
    "Gate B": [
        ("Transit Plaza", 400, "walking"),
        ("Gate A", 350, "shuttle"),
        ("Concourse East", 250, "walking")
    ],
    "Gate C": [
        ("Concourse West", 300, "walking"),
        ("Concourse East", 300, "walking")
    ],
    "Concourse West": [
        ("Transit Plaza", 600, "walking"),
        ("Gate A", 200, "walking"),
        ("Gate C", 300, "walking"),
        ("South Stand", 400, "walking")
    ],
    "Concourse East": [
        ("Transit Plaza", 500, "walking"),
        ("Gate B", 250, "walking"),
        ("Gate C", 300, "walking")
    ],
    "South Stand": [
        ("Transit Plaza", 200, "walking"),
        ("Concourse West", 400, "walking")
    ]
}

class RouteOptimizer:
    @staticmethod
    def calculate_cost(
        distance: float,
        mode: str,
        transit_alerts: Dict[str, TransitAlert],
        crowd_sensors: Dict[str, CrowdSensor],
        preference: str,
        accessible: bool,
        target_node_obj: Any
    ) -> float:
        # 1. Check accessibility constraint
        if accessible and target_node_obj:
            # Must support wheelchair ramp or elevator
            if not (target_node_obj.has_wheelchair_ramp or target_node_obj.has_elevator):
                return float('inf')

        # 2. Base walking speed (~80 meters per minute) or transit speed
        base_time = distance / 80.0 if mode == "walking" else distance / 300.0
        
        # 3. Add transit delays if applicable
        if mode in ["shuttle", "bus", "metro"]:
            matching_alert = next((a for r, a in transit_alerts.items() if mode in r.lower()), None)
            if matching_alert and matching_alert.status != "normal":
                base_time += matching_alert.delay_minutes
                if matching_alert.status == "suspended":
                    return float('inf')

        # 4. Crowd density penalty (only affects walking time)
        if mode == "walking" and target_node_obj.name in crowd_sensors:
            density = crowd_sensors[target_node_obj.name].density_percentage
            # Density above 70% slows walking down significantly
            if density > 70:
                base_time *= (1.0 + (density - 70) / 20.0)

        # 5. Apply preference multipliers
        if preference == "fastest":
            return base_time
        elif preference == "least_crowded" and target_node_obj.name in crowd_sensors:
            density = crowd_sensors[target_node_obj.name].density_percentage
            # Prioritize low density paths
            return base_time + (density * 5.0)
        elif preference == "safest":
            # Safest avoids extremely congested areas (>80%)
            density = crowd_sensors.get(target_node_obj.name, None)
            density_val = density.density_percentage if density else 0
            if density_val > 80:
                return base_time + 1000.0  # huge penalty
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
        accessible: bool = False
    ) -> Dict[str, Any]:
        # Index lookup dictionaries
        nodes_map = {n.name: n for n in nodes_list}
        alerts_map = {a.route: a for a in transit_alerts_list}
        sensors_map = {c.zone: c for c in crowd_sensors_list}

        if start not in STADIUM_GRAPH or end not in STADIUM_GRAPH:
            return {"error": "Invalid start or destination point"}

        # Dijkstra algorithm
        queue = [(0.0, start, [start], [])]
        visited = set()

        best_cost = float('inf')
        best_path = []
        best_modes = []

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
                
                if edge_cost == float('inf'):
                    continue

                heapq.heappush(queue, (cost + edge_cost, neighbor, path + [neighbor], modes + [transport_mode]))

        if best_cost == float('inf') or not best_path:
            # Fallback direct path representation
            return {
                "route": [start, end],
                "modes": ["walking"],
                "eta_minutes": 15,
                "preference": preference,
                "accessible": accessible,
                "verified": False,
                "note": "Offline direct corridor routing active."
            }

        return {
            "route": best_path,
            "modes": best_modes,
            "eta_minutes": round(best_cost, 1),
            "preference": preference,
            "accessible": accessible,
            "verified": True
        }
