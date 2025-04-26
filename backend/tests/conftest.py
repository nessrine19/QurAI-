import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from app.models.patient import CareSpecialist, Patient
import os
from sqlalchemy.pool import StaticPool

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.rollback()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    # Override the FastAPI dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close the session here, it's handled by the db_session fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clear the dependency override after test
    app.dependency_overrides.clear()

@pytest.fixture
def sample_care_specialist(db_session):
    care_specialist = CareSpecialist(
        specialist_id="CS001",
        first_name="John",
        last_name="Doe",
        email="john.doe@hospital.com",
        specialization="Oncology"
    )
    db_session.add(care_specialist)
    db_session.commit()
    return care_specialist

@pytest.fixture
def sample_patient(db_session, sample_care_specialist):
    patient = Patient(
        patient_id="P001",
        first_name="Jane",
        last_name="Smith",
        date_of_birth="1990-01-01",
        gender="Female",
        diagnosis="Cancer",
        tumor_location="Brain",
        tumor_stage="Stage 2",
        treatment_plan="Chemotherapy",
        notes="Initial diagnosis",
        care_specialist_id=sample_care_specialist.specialist_id,
        treatment_cycle=1,
        biomarkers={"marker1": "positive", "marker2": "negative"}
    )
    db_session.add(patient)
    db_session.commit()
    return patient 