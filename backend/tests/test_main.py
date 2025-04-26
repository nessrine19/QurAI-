import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import io
import csv
from app.main import app, preprocess_patient_data, predict_classification
from app.database import Base, get_db
from app.models.patient import Patient, CareSpecialist
import os
from sqlalchemy.pool import StaticPool
from unittest.mock import patch
from sqlalchemy.orm import Session
from sqlalchemy import desc
import time

# Use SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables after each test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def sample_care_specialist():
    return {
        "specialist_id": "CS001",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "specialization": "Oncology"
    }

@pytest.fixture
def sample_patient():
    return {
        "patient_id": "P001",
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1980-01-01",
        "gender": "F",
        "diagnosis": "Cancer",
        "tumor_location": "Lung",
        "tumor_stage": "Stage 1",
        "treatment_plan": "Radiation",
        "notes": "Test notes",
        "specialist_id": "CS001",
        "biomarkers": "EGFR+",
        "treatment_cycle": 1
    }

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to QurAI API"}

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_care_specialist(db_session, sample_care_specialist):
    response = client.post("/care-specialists/", json=sample_care_specialist)
    assert response.status_code == 200
    data = response.json()
    assert data["specialist_id"] == sample_care_specialist["specialist_id"]
    assert data["first_name"] == sample_care_specialist["first_name"]

def test_create_duplicate_care_specialist(db_session, sample_care_specialist):
    # First create
    client.post("/care-specialists/", json=sample_care_specialist)
    # Try to create again
    response = client.post("/care-specialists/", json=sample_care_specialist)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_get_care_specialist_patients(db_session, sample_care_specialist, sample_patient):
    # Create care specialist
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create patient
    patient_data = sample_patient.copy()
    patient_data["date_of_birth"] = datetime.strptime(patient_data["date_of_birth"], "%Y-%m-%d").date()
    patient = Patient(**patient_data)
    db_session.add(patient)
    db_session.commit()

    response = client.get(f"/care-specialists/{sample_care_specialist['specialist_id']}/patients")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == sample_patient["patient_id"]

def test_get_care_specialist_patients_not_found():
    response = client.get("/care-specialists/nonexistent/patients")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_get_patient(db_session, sample_care_specialist, sample_patient):
    # Create care specialist
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create patient
    patient_data = sample_patient.copy()
    patient_data["date_of_birth"] = datetime.strptime(patient_data["date_of_birth"], "%Y-%m-%d").date()
    patient = Patient(**patient_data)
    db_session.add(patient)
    db_session.commit()

    response = client.get(f"/patients/{sample_patient['patient_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == sample_patient["patient_id"]

def test_get_patient_not_found():
    response = client.get("/patients/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_upload_patients_csv(db_session, sample_care_specialist):
    # Create care specialist first
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create CSV content
    csv_content = """patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers
P001,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,CS001,EGFR+"""
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["patients_processed"] == 1

def test_upload_patients_csv_invalid_specialist():
    # Create CSV content with invalid specialist ID
    csv_content = """patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers
P001,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,INVALID,EGFR+"""
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]

def test_upload_patients_csv_duplicate_patient_ids(db_session, sample_care_specialist):
    # Create care specialist first
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create CSV content with duplicate patient IDs
    csv_content = """patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers
P001,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,CS001,EGFR+
P001,Jane,Smith,1985-02-02,F,Cancer,Breast,Stage 2,Chemo,Test notes 2,CS001,HER2+"""
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 400
    assert "Duplicate patient ID" in response.json()["detail"]

def test_upload_non_csv_file():
    response = client.post(
        "/upload/patients",
        files={"file": ("test.txt", "not a csv", "text/plain")}
    )
    assert response.status_code == 400
    assert "must be a CSV" in response.json()["detail"]

def test_upload_patients_csv_invalid_date_format(db_session, sample_care_specialist):
    # Create care specialist first
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create CSV content with invalid date format
    csv_content = """patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers
P001,John,Doe,01-01-1980,M,Cancer,Lung,Stage 1,Radiation,Test notes,CS001,EGFR+"""
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", csv_content, "text/csv")}
    )
    assert response.status_code == 400
    assert "Invalid data format" in response.json()["detail"]

def test_patient_treatment_cycle_increment(db_session, sample_care_specialist):
    # Create care specialist
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # First upload
    csv_content1 = """patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers
P002,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,CS001,EGFR+"""
    
    response1 = client.post(
        "/upload/patients",
        files={"file": ("patients1.csv", csv_content1, "text/csv")}
    )
    assert response1.status_code == 200

    # Wait a moment to ensure different timestamps
    time.sleep(0.1)

    # Second upload for same patient
    csv_content2 = """patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers
P002,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Updated notes,CS001,EGFR+"""
    
    response2 = client.post(
        "/upload/patients",
        files={"file": ("patients2.csv", csv_content2, "text/csv")}
    )
    assert response2.status_code == 200

    # Refresh the session to ensure we have the latest data
    db_session.expire_all()

    # Verify treatment cycle was incremented
    patient = db_session.query(Patient).filter(
        Patient.patient_id == "P002"
    ).order_by(desc(Patient.created_at)).first()
    assert patient.treatment_cycle == 2

def test_classify_patient_success(db_session, sample_care_specialist, sample_patient):
    # Create care specialist
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create patient
    patient_data = sample_patient.copy()
    patient_data["date_of_birth"] = datetime.strptime(patient_data["date_of_birth"], "%Y-%m-%d").date()
    patient = Patient(**patient_data)
    db_session.add(patient)
    db_session.commit()

    response = client.get(f"/patients/{sample_patient['patient_id']}/classify")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == sample_patient["patient_id"]
    assert "classifications" in data
    assert "confidence" in data

def test_classify_patient_not_found():
    response = client.get("/patients/nonexistent/classify")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_classify_patient_preprocessing_error(db_session, sample_care_specialist, sample_patient):
    # Create care specialist
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create patient with invalid data
    patient_data = sample_patient.copy()
    patient_data["date_of_birth"] = datetime.strptime(patient_data["date_of_birth"], "%Y-%m-%d").date()
    patient = Patient(**patient_data)
    db_session.add(patient)
    db_session.commit()

    # Mock preprocessing to raise an error
    def mock_preprocess(*args, **kwargs):
        raise Exception("Preprocessing error")

    import app.main
    app.main.preprocess_patient_data = mock_preprocess

    response = client.get(f"/patients/{sample_patient['patient_id']}/classify")
    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower()

def test_classify_patient_prediction_error(db_session, sample_care_specialist, sample_patient):
    # Create care specialist
    specialist = CareSpecialist(**sample_care_specialist)
    db_session.add(specialist)
    db_session.commit()

    # Create patient
    patient_data = sample_patient.copy()
    patient_data["date_of_birth"] = datetime.strptime(patient_data["date_of_birth"], "%Y-%m-%d").date()
    patient = Patient(**patient_data)
    db_session.add(patient)
    db_session.commit()

    # Mock prediction to raise an error
    def mock_predict(*args, **kwargs):
        raise Exception("Prediction error")

    import app.main
    app.main.predict_classification = mock_predict

    response = client.get(f"/patients/{sample_patient['patient_id']}/classify")
    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower()