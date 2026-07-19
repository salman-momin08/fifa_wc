"""
Stadium Operations Repository Layer.

Encapsulates all database query and persistence logic for Users, Incidents,
TransitAlerts, CrowdSensors, SOPRules, and WayfindingNodes using SQLAlchemy.
"""
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import CrowdSensor, Incident, SOPRule, TransitAlert, User, WayfindingNode


class StadiumRepository:
    """Repository class encapsulating stadium database data access operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository instance with active database session.

        Args:
            db: Active SQLAlchemy database session.
        """
        self.db = db

    # ── User Operations ──────────────────────────────────────────────────────

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Query User record by unique username.

        Args:
            username: Target username string.

        Returns:
            User model instance or None.
        """
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, user: User) -> User:
        """Persist new User record to database.

        Args:
            user: User model instance to add.

        Returns:
            Saved User model instance.
        """
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # ── Incident Operations ──────────────────────────────────────────────────

    def get_incidents(self) -> List[Incident]:
        """Retrieve all safety incidents ordered by timestamp descending.

        Returns:
            List of Incident records.
        """
        return self.db.query(Incident).order_by(Incident.timestamp.desc()).all()

    def get_incident_by_id(self, incident_id: int) -> Optional[Incident]:
        """Retrieve single Incident by primary key ID.

        Args:
            incident_id: Primary key incident ID.

        Returns:
            Incident model instance or None.
        """
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    def create_incident(self, incident: Incident) -> Incident:
        """Persist new Incident record to database.

        Args:
            incident: Incident instance to insert.

        Returns:
            Saved Incident model instance.
        """
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update_incident(self, incident: Incident) -> Incident:
        """Commit updates to an existing Incident record.

        Args:
            incident: Modified Incident instance.

        Returns:
            Refreshed Incident model instance.
        """
        self.db.commit()
        self.db.refresh(incident)
        return incident

    # ── Transit Alert Operations ─────────────────────────────────────────────

    def get_transit_alerts(self) -> List[TransitAlert]:
        """Retrieve all active transit alerts.

        Returns:
            List of TransitAlert records.
        """
        return self.db.query(TransitAlert).all()

    def get_transit_alert_by_route(self, route: str) -> Optional[TransitAlert]:
        """Retrieve transit alert by route name string.

        Args:
            route: Target route name.

        Returns:
            TransitAlert model instance or None.
        """
        return self.db.query(TransitAlert).filter(TransitAlert.route == route).first()

    def create_or_update_transit_alert(self, route: str, status: str, delay_minutes: int) -> TransitAlert:
        """Upsert transit alert status and delay minutes for a route.

        Args:
            route: Route name string.
            status: Transport status ('normal', 'delayed', 'suspended').
            delay_minutes: Delay duration in minutes.

        Returns:
            Saved TransitAlert instance.
        """
        alert = self.get_transit_alert_by_route(route)
        if alert:
            alert.status = status
            alert.delay_minutes = delay_minutes
        else:
            alert = TransitAlert(route=route, status=status, delay_minutes=delay_minutes)
            self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    # ── Crowd Sensor Operations ──────────────────────────────────────────────

    def get_crowd_sensors(self) -> List[CrowdSensor]:
        """Retrieve all crowd sensor zone telemetry records.

        Returns:
            List of CrowdSensor records.
        """
        return self.db.query(CrowdSensor).all()

    def get_crowd_sensor_by_zone(self, zone: str) -> Optional[CrowdSensor]:
        """Retrieve crowd sensor reading by zone name.

        Args:
            zone: Target zone name string.

        Returns:
            CrowdSensor model instance or None.
        """
        return self.db.query(CrowdSensor).filter(CrowdSensor.zone == zone).first()

    def create_or_update_crowd_sensor(
        self, zone: str, density_percentage: int, advisory: Optional[str]
    ) -> CrowdSensor:
        """Upsert crowd sensor density percentage and advisory for a zone.

        Args:
            zone: Target zone name string.
            density_percentage: Measured crowd density percentage (0-100).
            advisory: Optional AI or operator advisory text.

        Returns:
            Saved CrowdSensor instance.
        """
        sensor = self.get_crowd_sensor_by_zone(zone)
        if sensor:
            sensor.density_percentage = density_percentage
            sensor.advisory = advisory
        else:
            sensor = CrowdSensor(zone=zone, density_percentage=density_percentage, advisory=advisory)
            self.db.add(sensor)
        self.db.commit()
        self.db.refresh(sensor)
        return sensor

    # ── SOP Rule Operations ──────────────────────────────────────────────────

    def get_sop_rules(self) -> List[SOPRule]:
        """Retrieve all static Standard Operating Procedure (SOP) rules.

        Returns:
            List of SOPRule records.
        """
        return self.db.query(SOPRule).all()

    def get_sop_rule_by_gate_or_keyword(self, gate: str, title: str) -> Optional[SOPRule]:
        """Retrieve matching SOP rule by gate name or incident title keywords.

        Args:
            gate: Gate or zone name string.
            title: Incident title text for keyword search.

        Returns:
            Matching SOPRule instance or None.
        """
        sop = self.db.query(SOPRule).filter(
            or_(SOPRule.scenario.like(f"%{gate}%"), SOPRule.action_plan.like(f"%{gate}%"))
        ).first()

        if not sop:
            for kw in title.split():
                if len(kw) > 3:
                    sop = self.db.query(SOPRule).filter(SOPRule.scenario.like(f"%{kw}%")).first()
                    if sop:
                        break
        return sop

    # ── Wayfinding Node Operations ───────────────────────────────────────────

    def get_wayfinding_nodes(self) -> List[WayfindingNode]:
        """Retrieve all precinct wayfinding nodes and coordinates.

        Returns:
            List of WayfindingNode records.
        """
        return self.db.query(WayfindingNode).all()

    def get_wayfinding_node_by_name(self, name: str) -> Optional[WayfindingNode]:
        """Retrieve wayfinding node by name string.

        Args:
            name: Target node name.

        Returns:
            WayfindingNode model instance or None.
        """
        return self.db.query(WayfindingNode).filter(WayfindingNode.name == name).first()
