import os
import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL env var if set (PostgreSQL in Docker/production),
# otherwise fall back to local SQLite for development without Docker.
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "stadium_ops.db"))
    DATABASE_URL = f"sqlite:///{DB_PATH}"

_is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, default="draft")  # draft, active, resolved
    severity = Column(String, nullable=False)  # low, medium, high
    gate = Column(String, nullable=False)
    suggested_action = Column(String, nullable=True)
    is_approved = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class TransitAlert(Base):
    __tablename__ = "transit_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    route = Column(String, nullable=False)
    status = Column(String, nullable=False)  # normal, delayed, suspended
    delay_minutes = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class CrowdSensor(Base):
    __tablename__ = "crowd_sensors"
    
    id = Column(Integer, primary_key=True, index=True)
    zone = Column(String, nullable=False)
    density_percentage = Column(Integer, nullable=False)
    advisory = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SOPRule(Base):
    __tablename__ = "sop_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    scenario = Column(String, unique=True, nullable=False)
    action_plan = Column(String, nullable=False)

class WayfindingNode(Base):
    __tablename__ = "wayfinding_nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    zone = Column(String, nullable=False)
    has_wheelchair_ramp = Column(Boolean, default=False)
    has_elevator = Column(Boolean, default=False)
    has_escalator = Column(Boolean, default=False)
    restroom_nearby = Column(Boolean, default=False)
    first_aid_nearby = Column(Boolean, default=False)
    coordinates_lat = Column(Float, nullable=False)
    coordinates_lng = Column(Float, nullable=False)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="fan")  # fan, volunteer, organizer, admin
    is_active = Column(Boolean, default=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed default users
        if db.query(User).count() == 0:
            from app.core.security import get_password_hash
            users = [
                User(username="admin", hashed_password=get_password_hash("adminpassword"), role="admin"),
                User(username="organizer", hashed_password=get_password_hash("organizerpassword"), role="organizer"),
                User(username="volunteer", hashed_password=get_password_hash("volunteerpassword"), role="volunteer"),
                User(username="fan", hashed_password=get_password_hash("fanpassword"), role="fan"),
            ]
            db.bulk_save_objects(users)

        # Seed Wayfinding Nodes (Official Verified Coordinates)
        if db.query(WayfindingNode).count() == 0:
            nodes = [
                WayfindingNode(name="Gate A", zone="North Outer", has_wheelchair_ramp=True, has_elevator=True, restrooms_nearby=True, first_aid_nearby=True, coordinates_lat=45.4215, coordinates_lng=-75.6972),
                WayfindingNode(name="Gate B", zone="East Outer", has_wheelchair_ramp=True, has_elevator=False, restrooms_nearby=True, first_aid_nearby=False, coordinates_lat=45.4218, coordinates_lng=-75.6968),
                WayfindingNode(name="Gate C", zone="South Outer", has_wheelchair_ramp=False, has_elevator=False, restrooms_nearby=False, first_aid_nearby=False, coordinates_lat=45.4222, coordinates_lng=-75.6980),
                WayfindingNode(name="Transit Plaza", zone="South Outer", has_wheelchair_ramp=True, has_elevator=False, restrooms_nearby=True, first_aid_nearby=False, coordinates_lat=45.4200, coordinates_lng=-75.6950),
                WayfindingNode(name="Concourse West", zone="Inner Circle", has_wheelchair_ramp=True, has_elevator=True, restrooms_nearby=True, first_aid_nearby=True, coordinates_lat=45.4210, coordinates_lng=-75.7000),
                WayfindingNode(name="Concourse East", zone="Inner Circle", has_wheelchair_ramp=True, has_elevator=True, restrooms_nearby=True, first_aid_nearby=False, coordinates_lat=45.4230, coordinates_lng=-75.6940),
                WayfindingNode(name="South Stand", zone="Grandstand", has_wheelchair_ramp=False, has_elevator=False, restrooms_nearby=True, first_aid_nearby=False, coordinates_lat=45.4190, coordinates_lng=-75.6970),
            ]
            db.bulk_save_objects(nodes)
            
        # Seed SOP Rules (Static Emergency Guidelines)
        if db.query(SOPRule).count() == 0:
            sops = [
                SOPRule(scenario="Gate A Overcrowding", action_plan="1. Restrict new arrivals at Gate A entry point. 2. Activate dynamic signage redirection. 3. Instruct Volunteers at Transit Plaza to guide incoming fans to Gate B. 4. Initiate 10% gradual filter entry flow."),
                SOPRule(scenario="Medical Emergency South Stand", action_plan="1. Dispatch nearest first-aid squad from Concourse West. 2. Secure accessibility pathway to Gate C elevator. 3. Station a volunteer at Gate C entrance to receive paramedic vehicle."),
                SOPRule(scenario="Transit Delay Route 101", action_plan="1. Broadcast delay alert in multilingual fan channel. 2. Extend shuttle services on Route 102. 3. Notify volunteers at Concourse East to manage queue structures."),
                SOPRule(scenario="Suspicious Object Gate B", action_plan="1. Initiate localized perimeter cordon of 50 meters. 2. Request security supervisor verification. 3. Halt entry scans at Gate B, redirect new lines to Concourse East. 4. Keep alarms silent to prevent crowd crush."),
            ]
            db.bulk_save_objects(sops)
            
        # Seed Transit status
        if db.query(TransitAlert).count() == 0:
            alerts = [
                TransitAlert(route="Metro Line Red", status="normal", delay_minutes=0),
                TransitAlert(route="Shuttle Route 101", status="delayed", delay_minutes=15),
                TransitAlert(route="Shuttle Route 102", status="normal", delay_minutes=0),
                TransitAlert(route="West Parking Express", status="normal", delay_minutes=0),
            ]
            db.bulk_save_objects(alerts)
            
        # Seed Crowd sensors
        if db.query(CrowdSensor).count() == 0:
            sensors = [
                CrowdSensor(zone="Gate A", density_percentage=85, advisory="High Density (85%) - Slow entry flow, recommend redirection."),
                CrowdSensor(zone="Gate B", density_percentage=45, advisory="Moderate Density (45%) - Flowing smoothly."),
                CrowdSensor(zone="Gate C", density_percentage=30, advisory="Low Density (30%) - Entry clear."),
                CrowdSensor(zone="Transit Plaza", density_percentage=75, advisory="High Density (75%) - Dense queueing for bus transfers."),
            ]
            db.bulk_save_objects(sensors)
            
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Failed to seed database: {e}")
    finally:
        db.close()
