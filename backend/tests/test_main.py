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
def sample_care_specialist(db_session):
    specialist = CareSpecialist(
        specialist_id="CS001",
        first_name="John",
        last_name="Doe",
        email="john.doe@hospital.com",
        specialization="Oncology"
    )
    db_session.add(specialist)
    db_session.commit()
    db_session.refresh(specialist)
    return specialist

@pytest.fixture
def sample_patient(db_session, sample_care_specialist):
    patient = Patient(
        patient_id="P001",
        first_name="Jane",
        last_name="Smith",
        date_of_birth=date(1990, 1, 1),
        gender="F",
        diagnosis="Cancer",
        tumor_location="Breast",
        tumor_stage="Stage 2",
        treatment_plan="Chemotherapy",
        notes="Initial diagnosis",
        care_specialist_id=sample_care_specialist.specialist_id,
        treatment_cycle=1,
        biomarkers="HER2+"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to QurAI API"}

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_care_specialist(client):
    specialist_data = {
        "specialist_id": "CS002",
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@hospital.com",
        "specialization": "Radiology"
    }
    response = client.post("/care-specialists/", json=specialist_data)
    assert response.status_code == 200
    data = response.json()
    assert data["specialist_id"] == specialist_data["specialist_id"]
    assert data["email"] == specialist_data["email"]

def test_create_duplicate_care_specialist(client, sample_care_specialist):
    specialist_data = {
        "specialist_id": sample_care_specialist.specialist_id,
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@hospital.com",
        "specialization": "Radiology"
    }
    response = client.post("/care-specialists/", json=specialist_data)
    assert response.status_code == 400

def test_get_care_specialist_patients(client, sample_care_specialist, sample_patient):
    response = client.get(f"/care-specialists/{sample_care_specialist.specialist_id}/patients")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["patient_id"] == sample_patient.patient_id

def test_get_care_specialist_patients_not_found(client):
    response = client.get("/care-specialists/nonexistent/patients")
    assert response.status_code == 404

def test_get_patient(client, sample_patient):
    response = client.get(f"/patients/{sample_patient.patient_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == sample_patient.patient_id
    assert data["first_name"] == sample_patient.first_name

def test_get_patient_not_found(client):
    response = client.get("/patients/nonexistent")
    assert response.status_code == 404

def test_upload_patients_csv(client, sample_care_specialist):
    # Create CSV content
    csv_content = "patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers\n"
    csv_content += f"P002,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,{sample_care_specialist.specialist_id},EGFR+"
    
    # Create file-like object
    file = io.BytesIO(csv_content.encode())
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", file, "text/csv")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["patients_processed"] == 1

def test_upload_patients_csv_invalid_specialist(client):
    csv_content = "patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers\n"
    csv_content += "P002,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,INVALID,EGFR+"
    
    file = io.BytesIO(csv_content.encode())
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", file, "text/csv")}
    )
    assert response.status_code == 400

def test_upload_patients_csv_duplicate_patient_ids(client):
    csv_content = "patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers\n"
    csv_content += "P002,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,CS001,EGFR+\n"
    csv_content += "P002,Jane,Smith,1985-01-01,F,Cancer,Breast,Stage 2,Chemo,Other notes,CS001,HER2+"
    
    file = io.BytesIO(csv_content.encode())
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", file, "text/csv")}
    )
    assert response.status_code == 400

def test_upload_non_csv_file(client):
    file = io.BytesIO(b"not a csv file")
    response = client.post(
        "/upload/patients",
        files={"file": ("test.txt", file, "text/plain")}
    )
    assert response.status_code == 400

def test_upload_patients_csv_invalid_date_format(client):
    csv_content = "patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers\n"
    csv_content += "P002,John,Doe,01-01-1980,M,Cancer,Lung,Stage 1,Radiation,Test notes,CS001,EGFR+"
    
    file = io.BytesIO(csv_content.encode())
    
    response = client.post(
        "/upload/patients",
        files={"file": ("patients.csv", file, "text/csv")}
    )
    assert response.status_code == 400

def test_patient_treatment_cycle_increment(client, db_session, sample_care_specialist):
    # First upload
    csv_content = "patient_id,first_name,last_name,date_of_birth,gender,diagnosis,tumor_location,tumor_stage,treatment_plan,notes,specialist_id,biomarkers\n"
    csv_content += f"P002,John,Doe,1980-01-01,M,Cancer,Lung,Stage 1,Radiation,Test notes,{sample_care_specialist.specialist_id},EGFR+"
    
    file = io.BytesIO(csv_content.encode())
    response = client.post("/upload/patients", files={"file": ("patients.csv", file, "text/csv")})
    if response.status_code != 200:
        print(f"First upload failed: {response.json()}")
    assert response.status_code == 200
    db_session.commit()  # Commit the first upload
    
    # Second upload (same patient)
    file.seek(0)
    response = client.post("/upload/patients", files={"file": ("patients.csv", file, "text/csv")})
    if response.status_code != 200:
        print(f"Second upload failed: {response.json()}")
    assert response.status_code == 200
    db_session.commit()  # Commit the second upload
    
    # Check if treatment cycle incremented
    db_session.expire_all()  # Expire all objects to ensure we get fresh data
    patient = db_session.query(Patient).filter(Patient.patient_id == "P002").order_by(Patient.created_at.desc()).first()
    assert patient.treatment_cycle == 2

def test_classify_patient_success(client, sample_patient):
    # Mock the preprocessing and prediction functions
    with patch('app.main.preprocess_patient_data') as mock_preprocess, \
         patch('app.main.predict_classification') as mock_predict:
        
        # Setup mock return values
        mock_preprocess.return_value = {
            "age": 30.0,
            "treatment_cycle": 1,
            "tumor_stage": "Stage 2",
            "biomarkers": "HER2+"
        }
        
        mock_predict.return_value = {
            "complete_remission": 0.6,
            "partial_remission": 0.3,
            "stable_disease": 0.1,
            "progressive_disease": 0.0
        }
        
        # Make the request
        response = client.get(f"/patients/{sample_patient.patient_id}/classify")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["patient_id"] == sample_patient.patient_id
        assert data["classifications"]["complete_remission"] == 0.6
        assert data["confidence"] == 0.6
        
        # Verify mocks were called correctly
        mock_preprocess.assert_called_once()
        mock_predict.assert_called_once_with(mock_preprocess.return_value)

def test_classify_patient_not_found(client):
    response = client.get("/patients/nonexistent/classify")
    assert response.status_code == 404
    assert response.json()["detail"] == "Patient not found"

def test_classify_patient_preprocessing_error(client, sample_patient):
    # Mock the preprocessing function to raise an exception
    with patch('app.main.preprocess_patient_data') as mock_preprocess:
        mock_preprocess.side_effect = Exception("Preprocessing error")
        
        response = client.get(f"/patients/{sample_patient.patient_id}/classify")
        assert response.status_code == 500

def test_classify_patient_prediction_error(client, sample_patient):
    # Mock the preprocessing and prediction functions
    with patch('app.main.preprocess_patient_data') as mock_preprocess, \
         patch('app.main.predict_classification') as mock_predict:
        
        # Setup mock return values
        mock_preprocess.return_value = {
            "age": 30.0,
            "treatment_cycle": 1,
            "tumor_stage": "Stage 2",
            "biomarkers": "HER2+"
        }
        
        # Make prediction function raise an exception
        mock_predict.side_effect = Exception("Prediction error")
        
        response = client.get(f"/patients/{sample_patient.patient_id}/classify")
        assert response.status_code == 500