from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import pandas as pd
import os
from dotenv import load_dotenv
import joblib

load_dotenv()

# Initialize Flask application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure database connection using environment variable
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)


db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Define CareSpecialist model for database
class CareSpecialist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    patients = db.relationship('Patient', backref='care_specialist', lazy=True)

# Define Patient model with all required medical features
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    diagnosis = db.Column(db.String(50))
    # Mean features
    radius_mean = db.Column(db.Float)
    texture_mean = db.Column(db.Float)
    perimeter_mean = db.Column(db.Float)
    area_mean = db.Column(db.Float)
    smoothness_mean = db.Column(db.Float)
    compactness_mean = db.Column(db.Float)
    concavity_mean = db.Column(db.Float)
    concave_points_mean = db.Column(db.Float)
    symmetry_mean = db.Column(db.Float)
    fractal_dimension_mean = db.Column(db.Float)
    # Standard error features
    radius_se = db.Column(db.Float)
    texture_se = db.Column(db.Float)
    perimeter_se = db.Column(db.Float)
    area_se = db.Column(db.Float)
    smoothness_se = db.Column(db.Float)
    compactness_se = db.Column(db.Float)
    concavity_se = db.Column(db.Float)
    concave_points_se = db.Column(db.Float)
    symmetry_se = db.Column(db.Float)
    fractal_dimension_se = db.Column(db.Float)
    # Worst features
    radius_worst = db.Column(db.Float)
    texture_worst = db.Column(db.Float)
    perimeter_worst = db.Column(db.Float)
    area_worst = db.Column(db.Float)
    smoothness_worst = db.Column(db.Float)
    compactness_worst = db.Column(db.Float)
    concavity_worst = db.Column(db.Float)
    concave_points_worst = db.Column(db.Float)
    symmetry_worst = db.Column(db.Float)
    fractal_dimension_worst = db.Column(db.Float)
    # Foreign key relationship to care specialist
    care_specialist_id = db.Column(db.Integer, db.ForeignKey('care_specialist.id'), nullable=False)

# API endpoint to create a new care specialist
@app.route('/api/care-specialist', methods=['POST'])
def create_care_specialist():
    data = request.get_json()
    new_specialist = CareSpecialist(
        name=data['name'],
        email=data['email']
    )
    db.session.add(new_specialist)
    db.session.commit()
    return jsonify({'id': new_specialist.id, 'name': new_specialist.name, 'email': new_specialist.email}), 201

# API endpoint to upload patient data via CSV file
@app.route('/api/upload-patients/<int:specialist_id>', methods=['POST'])
def upload_patients(specialist_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
        # Read and validate CSV file
        df = pd.read_csv(file)
        required_columns = [
            'id', 'diagnosis', 'radius_mean', 'texture_mean', 'perimeter_mean',
            'area_mean', 'smoothness_mean', 'compactness_mean', 'concavity_mean',
            'concave_points_mean', 'symmetry_mean', 'fractal_dimension_mean',
            'radius_se', 'texture_se', 'perimeter_se', 'area_se', 'smoothness_se',
            'compactness_se', 'concavity_se', 'concave_points_se', 'symmetry_se',
            'fractal_dimension_se', 'radius_worst', 'texture_worst', 'perimeter_worst',
            'area_worst', 'smoothness_worst', 'compactness_worst', 'concavity_worst',
            'concave_points_worst', 'symmetry_worst', 'fractal_dimension_worst'
        ]
        
        # Validate required columns
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV missing required columns'}), 400

        # Check for duplicate patient IDs
        if len(df['id'].unique()) != len(df):
            return jsonify({'error': 'Duplicate patient IDs found in upload'}), 400

        # Process each row in the CSV
        for _, row in df.iterrows():
            patient = Patient.query.get(row['id'])
            if patient:
                # Update existing patient
                for col in required_columns:
                    setattr(patient, col, row[col])
            else:
                # Create new patient
                new_patient = Patient(
                    id=row['id'],
                    care_specialist_id=specialist_id,
                    **{col: row[col] for col in required_columns[1:]}
                )
                db.session.add(new_patient)

        db.session.commit()
        return jsonify({'message': 'Patients uploaded successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# API endpoint to get patient details
@app.route('/api/patient/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Format patient data for response
    patient_data = {
        'id': patient.id,
        'diagnosis': patient.diagnosis,
        'radius_mean': patient.radius_mean,
        'texture_mean': patient.texture_mean,
        'perimeter_mean': patient.perimeter_mean,
        'area_mean': patient.area_mean,
        'smoothness_mean': patient.smoothness_mean,
        'compactness_mean': patient.compactness_mean,
        'concavity_mean': patient.concavity_mean,
        'concave_points_mean': patient.concave_points_mean,
        'symmetry_mean': patient.symmetry_mean,
        'fractal_dimension_mean': patient.fractal_dimension_mean,
        'radius error': patient.radius_se,
        'texture_se': patient.texture_se,
        'perimeter_se': patient.perimeter_se,
        'area_se': patient.area_se,
        'smoothness_se': patient.smoothness_se,
        'compactness_se': patient.compactness_se,
        'concavity_se': patient.concavity_se,
        'concave_points_se': patient.concave_points_se,
        'symmetry_se': patient.symmetry_se,
        'fractal_dimension_se': patient.fractal_dimension_se,
        'worst radius': patient.radius_worst,
        'texture_worst': patient.texture_worst,
        'perimeter_worst': patient.perimeter_worst,
        'worst area': patient.area_worst,
        'smoothness_worst': patient.smoothness_worst,
        'compactness_worst': patient.compactness_worst,
        'concavity_worst': patient.concavity_worst,
        'worst concave points': patient.concave_points_worst,
        'symmetry_worst': patient.symmetry_worst,
        'fractal_dimension_worst': patient.fractal_dimension_worst
    }
    return jsonify(patient_data), 200

# API endpoint to get care specialist details
@app.route('/api/care-specialist/<int:specialist_id>', methods=['GET'])
def get_care_specialist(specialist_id):
    specialist = CareSpecialist.query.get(specialist_id)
    if not specialist:
        return jsonify({'error': 'Care specialist not found'}), 404
    
    specialist_data = {
        'id': specialist.id,
        'name': specialist.name,
        'email': specialist.email,
        'patient_ids': [patient.id for patient in specialist.patients]
    }
    return jsonify(specialist_data), 200

# Preprocess patient data for classification
def preprocess(data_dict, scaler_path='../classification:/scaler.pkl'):
    """
    Preprocess patient data for classification:
    1. Select relevant features
    2. Convert to DataFrame
    3. Standardize using pre-fitted scaler
    4. Return standardized values
    """
    # Define selected features for classification
    selected_features = [
        'radius error',
        'worst radius',
        'worst area',
        'worst concave points'
    ]

    # Convert input dict to DataFrame
    df = pd.DataFrame([data_dict])

    # Select and convert features to numeric
    data_sel = df[selected_features].apply(pd.to_numeric, errors='coerce')

    # Load and apply pre-fitted scaler
    scaler = joblib.load(scaler_path)
    standardized = scaler.transform(data_sel)

    # Return standardized features as dict
    return {feat: float(val)
            for feat, val in zip(selected_features, standardized.flatten())}

# Perform classification using preprocessed data
def classification(preprocessed_data, model_path='../classification:/qsvc_model.pkl'):
    """
    Classify patient data using quantum support vector classifier:
    1. Load pre-trained model
    2. Make prediction
    3. Return probabilities for each class
    """
    values = list(preprocessed_data.values())
    model = joblib.load(model_path)
    prediction = list(model.predict_proba(values)[0])
    return {
        'malignant': float(prediction[0]),
        'benign': float(prediction[1])
    }

# API endpoint for patient classification
@app.route('/api/classify/<int:patient_id>', methods=['GET'])
def classify_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    # Format patient data for classification
    patient_data = {
        'id': patient.id,
        'diagnosis': patient.diagnosis,
        'radius_mean': patient.radius_mean,
        'texture_mean': patient.texture_mean,
        'perimeter_mean': patient.perimeter_mean,
        'area_mean': patient.area_mean,
        'smoothness_mean': patient.smoothness_mean,
        'compactness_mean': patient.compactness_mean,
        'concavity_mean': patient.concavity_mean,
        'concave_points_mean': patient.concave_points_mean,
        'symmetry_mean': patient.symmetry_mean,
        'fractal_dimension_mean': patient.fractal_dimension_mean,
        'radius error': patient.radius_se,
        'texture_se': patient.texture_se,
        'perimeter_se': patient.perimeter_se,
        'area_se': patient.area_se,
        'smoothness_se': patient.smoothness_se,
        'compactness_se': patient.compactness_se,
        'concavity_se': patient.concavity_se,
        'concave_points_se': patient.concave_points_se,
        'symmetry_se': patient.symmetry_se,
        'fractal_dimension_se': patient.fractal_dimension_se,
        'worst radius': patient.radius_worst,
        'texture_worst': patient.texture_worst,
        'perimeter_worst': patient.perimeter_worst,
        'worst area': patient.area_worst,
        'smoothness_worst': patient.smoothness_worst,
        'compactness_worst': patient.compactness_worst,
        'concavity_worst': patient.concavity_worst,
        'worst concave points': patient.concave_points_worst,
        'symmetry_worst': patient.symmetry_worst,
        'fractal_dimension_worst': patient.fractal_dimension_worst
    }
    
    try:
        # Preprocess and classify patient data
        preprocessed_data = preprocess(patient_data)
        classification_result = classification(preprocessed_data)
        return jsonify(classification_result), 200
    except Exception as e:
        return jsonify({'error': f'Error during classification: {str(e)}'}), 500

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint to verify API is running
    """
    return jsonify({'status': 'ready'}), 200

# Run the application
if __name__ == '__main__':
    app.run(debug=True) 