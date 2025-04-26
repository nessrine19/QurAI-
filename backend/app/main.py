from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models.patient import Patient, PatientCSV, CareSpecialist, CareSpecialistBase, PatientResponse
from .database import get_db, Base, engine
from typing import List, Dict, Set
from pydantic import BaseModel

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="QurAI API",
    description="""
    QurAI API - Cancer Treatment Optimization and Radiotherapy Planning System
    
    This API provides endpoints for managing cancer patients, care specialists, and treatment data.
    It includes features for:
    - Patient data management
    - Care specialist management
    - Treatment cycle tracking
    - Patient classification and outcome prediction
    - Secure data handling with encryption
    
    The system uses PostgreSQL for data storage and includes encryption for sensitive patient information.
    """,
    version="1.0.0",
    contact={
        "name": "QurAI Team",
        "email": "support@qurai.com",
    },
    license_info={
        "name": "MIT",
    },
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        dict: A welcome message
    """
    return {"message": "Welcome to QurAI API"}

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    
    Returns:
        dict: Status of the API
    """
    return {"status": "healthy"}

@app.post("/care-specialists/", response_model=CareSpecialistBase, tags=["Care Specialists"])
async def create_care_specialist(care_specialist: CareSpecialistBase, db: Session = Depends(get_db)):
    """
    Create a new care specialist.
    
    Args:
        care_specialist (CareSpecialistBase): Care specialist data including:
            - specialist_id: Unique identifier for the specialist
            - first_name: Specialist's first name
            - last_name: Specialist's last name
            - email: Specialist's email address
            - specialization: Area of medical specialization
    
    Returns:
        CareSpecialistBase: The created care specialist
    
    Raises:
        HTTPException: If specialist ID already exists or if there's an error creating the specialist
    """
    # Check if specialist ID already exists
    existing_specialist = db.query(CareSpecialist).filter(
        CareSpecialist.specialist_id == care_specialist.specialist_id
    ).first()
    if existing_specialist:
        raise HTTPException(
            status_code=400,
            detail=f"Care specialist with ID {care_specialist.specialist_id} already exists"
        )

    try:
        db_care_specialist = CareSpecialist(
            specialist_id=care_specialist.specialist_id,
            first_name=care_specialist.first_name,
            last_name=care_specialist.last_name,
            email=care_specialist.email,
            specialization=care_specialist.specialization
        )
        db.add(db_care_specialist)
        db.commit()
        db.refresh(db_care_specialist)
        return db_care_specialist
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/care-specialists/{specialist_id}/patients", response_model=List[PatientResponse], tags=["Care Specialists"])
async def get_care_specialist_patients(specialist_id: str, db: Session = Depends(get_db)):
    """
    Get all patients associated with a specific care specialist.
    
    Args:
        specialist_id (str): The ID of the care specialist
    
    Returns:
        List[PatientResponse]: List of patients under the care specialist
    
    Raises:
        HTTPException: If the care specialist is not found
    """
    # First get the care specialist
    care_specialist = db.query(CareSpecialist).filter(CareSpecialist.specialist_id == specialist_id).first()
    if not care_specialist:
        raise HTTPException(status_code=404, detail="Care specialist not found")
    
    # Get all patients for this care specialist
    patients = db.query(Patient).filter(
        Patient.care_specialist_id == specialist_id
    ).order_by(
        Patient.patient_id,
        desc(Patient.created_at)
    ).distinct(
        Patient.patient_id
    ).all()
    
    return patients

@app.get("/patients/{patient_id}", response_model=PatientResponse, tags=["Patients"])
async def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """
    Get the latest record for a specific patient.
    
    Args:
        patient_id (str): The ID of the patient
    
    Returns:
        PatientResponse: The patient's latest record
    
    Raises:
        HTTPException: If the patient is not found
    """
    # Get the latest record for the patient
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).order_by(
        desc(Patient.created_at)
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    return patient

@app.post("/upload/patients", tags=["Patients"])
async def upload_patients_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload patient data via CSV file.
    
    The CSV file should contain the following columns:
    - patient_id: Unique identifier for the patient
    - first_name: Patient's first name
    - last_name: Patient's last name
    - date_of_birth: Patient's date of birth (YYYY-MM-DD format)
    - gender: Patient's gender
    - diagnosis: Medical diagnosis
    - tumor_location: Location of the tumor
    - tumor_stage: Stage of the tumor
    - treatment_plan: Treatment plan details
    - notes: Additional notes
    - specialist_id: ID of the assigned care specialist
    - biomarkers: Biomarker information
    
    Args:
        file (UploadFile): CSV file containing patient data
    
    Returns:
        JSONResponse: Success message and number of patients processed
    
    Raises:
        HTTPException: If the file is not a CSV, contains invalid data, or if there are duplicate patient IDs
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        # Read the CSV file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode('utf-8'))
        csv_reader = csv.DictReader(csv_file)
        
        # Track patient IDs in this upload to detect duplicates
        seen_patient_ids: Set[str] = set()
        patients_to_add = []
        
        # Process each row
        for row in csv_reader:
            try:
                # Convert the row to a PatientCSV model
                patient_data = PatientCSV(**row)
                
                # Check for duplicates in this upload
                if patient_data.patient_id in seen_patient_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Duplicate patient ID {patient_data.patient_id} found in the same upload"
                    )
                seen_patient_ids.add(patient_data.patient_id)
                
                # Get the care specialist
                care_specialist = db.query(CareSpecialist).filter(
                    CareSpecialist.specialist_id == patient_data.specialist_id
                ).first()
                
                if not care_specialist:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Care specialist with ID {patient_data.specialist_id} not found"
                    )
                
                try:
                    # Convert date string to date object
                    date_of_birth = datetime.strptime(patient_data.date_of_birth, "%Y-%m-%d").date()
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid date format for patient {patient_data.patient_id}. Use YYYY-MM-DD format."
                    )
                
                # Get the latest treatment cycle for this patient
                latest_patient = db.query(Patient).filter(
                    Patient.patient_id == patient_data.patient_id
                ).order_by(
                    desc(Patient.created_at)
                ).first()
                
                # Calculate next treatment cycle
                next_cycle = 1
                if latest_patient:
                    next_cycle = latest_patient.treatment_cycle + 1
                
                # Create database model instance
                db_patient = Patient(
                    patient_id=patient_data.patient_id,
                    first_name=patient_data.first_name,
                    last_name=patient_data.last_name,
                    date_of_birth=date_of_birth,
                    gender=patient_data.gender,
                    diagnosis=patient_data.diagnosis,
                    tumor_location=patient_data.tumor_location,
                    tumor_stage=patient_data.tumor_stage,
                    treatment_plan=patient_data.treatment_plan,
                    notes=patient_data.notes,
                    care_specialist_id=patient_data.specialist_id,
                    treatment_cycle=next_cycle,
                    biomarkers=patient_data.biomarkers
                )
                
                patients_to_add.append(db_patient)
                
            except HTTPException as he:
                db.rollback()
                raise he
            except Exception as e:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data in row: {row}. Error: {str(e)}"
                )
        
        try:
            # Add all patients to database
            for patient in patients_to_add:
                db.add(patient)
            
            # Commit all changes
            db.commit()
            
            return JSONResponse(
                content={
                    "message": f"Successfully processed and stored {len(patients_to_add)} patients",
                    "patients_processed": len(patients_to_add)
                }
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Error saving patients to database: {str(e)}"
            )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error processing file: {str(e)}"
        )

class ClassificationResult(BaseModel):
    """
    Model representing the classification results for a patient.
    
    Attributes:
        patient_id (str): ID of the patient
        classifications (Dict[str, float]): Probability distribution over possible classifications
        confidence (float): Confidence score for the prediction
    """
    patient_id: str
    classifications: Dict[str, float]
    confidence: float

def preprocess_patient_data(patient: Patient) -> Dict:
    """
    Preprocess patient data for ML model input.
    
    This function transforms patient data into features suitable for the ML model.
    Currently a dummy implementation that will be replaced with actual preprocessing logic.
    
    Args:
        patient (Patient): Patient data to preprocess
    
    Returns:
        Dict: Preprocessed features including:
            - age: Patient's age in years
            - treatment_cycle: Current treatment cycle number
            - tumor_stage: Stage of the tumor
            - biomarkers: Biomarker information
    """
    # In reality, this would do feature engineering, normalization, etc.
    return {
        "age": (datetime.now().date() - patient.date_of_birth).days / 365,
        "treatment_cycle": patient.treatment_cycle,
        "tumor_stage": patient.tumor_stage,
        "biomarkers": patient.biomarkers
    }

def predict_classification(preprocessed_data: Dict) -> Dict[str, float]:
    """
    Predict patient classification using ML model.
    
    This function takes preprocessed patient data and returns a probability distribution
    over possible classifications. Currently a dummy implementation that will be replaced
    with actual ML model predictions.
    
    Args:
        preprocessed_data (Dict): Preprocessed patient features
    
    Returns:
        Dict[str, float]: Probability distribution over classifications:
            - complete_remission: Probability of complete remission
            - partial_remission: Probability of partial remission
            - stable_disease: Probability of stable disease
            - progressive_disease: Probability of progressive disease
    """
    # In reality, this would use a trained ML model
    # For now, return dummy probabilities
    return {
        "complete_remission": 0.6,
        "partial_remission": 0.3,
        "stable_disease": 0.1,
        "progressive_disease": 0.0
    }

@app.get("/patients/{patient_id}/classify", response_model=ClassificationResult, tags=["Classification"])
async def classify_patient(patient_id: str, db: Session = Depends(get_db)):
    """
    Classify a patient's treatment outcome.
    
    This endpoint:
    1. Retrieves the patient's latest record
    2. Preprocesses the patient data
    3. Runs the ML model to predict treatment outcomes
    4. Returns the classification results with confidence scores
    
    Args:
        patient_id (str): ID of the patient to classify
    
    Returns:
        ClassificationResult: Classification results including:
            - patient_id: ID of the patient
            - classifications: Probability distribution over possible outcomes
            - confidence: Confidence score for the prediction
    
    Raises:
        HTTPException: If the patient is not found or if there's an error in preprocessing/prediction
    """
    # Get the latest record for the patient
    patient = db.query(Patient).filter(
        Patient.patient_id == patient_id
    ).order_by(
        desc(Patient.created_at)
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    try:
        # Preprocess the patient data
        preprocessed_data = preprocess_patient_data(patient)
        
        # Get classification predictions
        classifications = predict_classification(preprocessed_data)
        
        # Calculate confidence (dummy implementation)
        confidence = max(classifications.values())
        
        return ClassificationResult(
            patient_id=patient.patient_id,
            classifications=classifications,
            confidence=confidence
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 