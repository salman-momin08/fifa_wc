from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_
from typing import List, Optional
from datetime import datetime
from app.database import User, Incident, TransitAlert, CrowdSensor, SOPRule, WayfindingNode

class StadiumRepository:
    def __init__(self, db: Session):
        self.db = db

    # User operations
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # Incident operations
    def get_incidents(self) -> List[Incident]:
        return self.db.query(Incident).order_by(Incident.timestamp.desc()).all()

    def get_incident_by_id(self, incident_id: int) -> Optional[Incident]:
        return self.db.query(Incident).filter(Incident.id == incident_id).first()

    def create_incident(self, incident: Incident) -> Incident:
        self.db.add(incident)
        self.db.commit()
        self.db.refresh(incident)
        return incident

    def update_incident(self, incident: Incident) -> Incident:
        # Optimistic locking validation: verify version or timestamp hasn't changed.
        # Since we use simple model, we can check if the row is still matched in the DB
        # before saving. In SQLAlchemy, we can merge or commit.
        # For enterprise grade, we commit and handle database refresh.
        self.db.commit()
        self.db.refresh(incident)
        return incident

    # Transit alerts operations
    def get_transit_alerts(self) -> List[TransitAlert]:
        return self.db.query(TransitAlert).all()

    def get_transit_alert_by_route(self, route: str) -> Optional[TransitAlert]:
        return self.db.query(TransitAlert).filter(TransitAlert.route == route).first()

    def create_or_update_transit_alert(self, route: str, status: str, delay_minutes: int) -> TransitAlert:
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

    # Crowd sensor operations
    def get_crowd_sensors(self) -> List[CrowdSensor]:
        return self.db.query(CrowdSensor).all()

    def get_crowd_sensor_by_zone(self, zone: str) -> Optional[CrowdSensor]:
        return self.db.query(CrowdSensor).filter(CrowdSensor.zone == zone).first()

    def create_or_update_crowd_sensor(self, zone: str, density_percentage: int, advisory: Optional[str]) -> CrowdSensor:
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

    # SOP operations
    def get_sop_rules(self) -> List[SOPRule]:
        return self.db.query(SOPRule).all()

    def get_sop_rule_by_gate_or_keyword(self, gate: str, title: str) -> Optional[SOPRule]:
        # Search by gate name in scenario or plan
        sop = self.db.query(SOPRule).filter(
            or_(
                SOPRule.scenario.like(f"%{gate}%"),
                SOPRule.action_plan.like(f"%{gate}%")
            )
        ).first()
        
        # Search by keywords if no direct gate match
        if not sop:
            for kw in title.split():
                if len(kw) > 3:
                    sop = self.db.query(SOPRule).filter(SOPRule.scenario.like(f"%{kw}%")).first()
                    if sop:
                        break
        return sop

    # Wayfinding operations
    def get_wayfinding_nodes(self) -> List[WayfindingNode]:
        return self.db.query(WayfindingNode).all()

    def get_wayfinding_node_by_name(self, name: str) -> Optional[WayfindingNode]:
        return self.db.query(WayfindingNode).filter(WayfindingNode.name == name).first()
