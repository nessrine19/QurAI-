from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import pandas as pd
import os
from dotenv import load_dotenv
import joblib

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

class CareSpecialist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    patients = db.relationship('Patient', backref='care_specialist', lazy=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    diagnosis = db.Column(db.String(50))
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
    care_specialist_id = db.Column(db.Integer, db.ForeignKey('care_specialist.id'), nullable=False)

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

@app.route('/api/upload-patients/<int:specialist_id>', methods=['POST'])
def upload_patients(specialist_id):
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be a CSV'}), 400

    try:
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
        
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': 'CSV missing required columns'}), 400

        # Check for duplicate IDs in the current upload
        if len(df['id'].unique()) != len(df):
            return jsonify({'error': 'Duplicate patient IDs found in upload'}), 400

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

@app.route('/api/patient/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
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
        'radius_se': patient.radius_se,
        'texture_se': patient.texture_se,
        'perimeter_se': patient.perimeter_se,
        'area_se': patient.area_se,
        'smoothness_se': patient.smoothness_se,
        'compactness_se': patient.compactness_se,
        'concavity_se': patient.concavity_se,
        'concave_points_se': patient.concave_points_se,
        'symmetry_se': patient.symmetry_se,
        'fractal_dimension_se': patient.fractal_dimension_se,
        'radius_worst': patient.radius_worst,
        'texture_worst': patient.texture_worst,
        'perimeter_worst': patient.perimeter_worst,
        'area_worst': patient.area_worst,
        'smoothness_worst': patient.smoothness_worst,
        'compactness_worst': patient.compactness_worst,
        'concavity_worst': patient.concavity_worst,
        'concave_points_worst': patient.concave_points_worst,
        'symmetry_worst': patient.symmetry_worst,
        'fractal_dimension_worst': patient.fractal_dimension_worst
    }
    return jsonify(patient_data), 200

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

def preprocess(data_dict, scaler_path='scaler.pkl'):
    """
    Given a dict of raw feature values, pick a fixed subset of features,
    standardize them using a pre‐fitted StandardScaler, and return a dict
    of the scaled values.
    """
    # 1) Define your selected features here
    selected_features = [
        'radius_se',
        'radius_worst',
        'area_worst',
        'concave points_mean'
    ]

    # 2) Turn the input dict into a 1‐row DataFrame
    df = pd.DataFrame([data_dict])

    # 3) Select & coerce to numeric
    data_sel = df[selected_features].apply(pd.to_numeric, errors='coerce')

    # 4) Load your fitted scaler and apply it
    scaler = joblib.load(scaler_path)
    standardized = scaler.transform(data_sel)

    # 5) Return a flat dict of feature → scaled value
    return {feat: float(val)
            for feat, val in zip(selected_features, standardized.flatten())}

def dummy_classification(preprocessed_data):
    # This is a placeholder for the actual classification model
    return {
        'malignant': 0.7,
        'benign': 0.3
    }

@app.route('/api/classify/<int:patient_id>', methods=['GET'])
def classify_patient(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    patient_data = {
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
        'radius_se': patient.radius_se,
        'texture_se': patient.texture_se,
        'perimeter_se': patient.perimeter_se,
        'area_se': patient.area_se,
        'smoothness_se': patient.smoothness_se,
        'compactness_se': patient.compactness_se,
        'concavity_se': patient.concavity_se,
        'concave_points_se': patient.concave_points_se,
        'symmetry_se': patient.symmetry_se,
        'fractal_dimension_se': patient.fractal_dimension_se,
        'radius_worst': patient.radius_worst,
        'texture_worst': patient.texture_worst,
        'perimeter_worst': patient.perimeter_worst,
        'area_worst': patient.area_worst,
        'smoothness_worst': patient.smoothness_worst,
        'compactness_worst': patient.compactness_worst,
        'concavity_worst': patient.concavity_worst,
        'concave_points_worst': patient.concave_points_worst,
        'symmetry_worst': patient.symmetry_worst,
        'fractal_dimension_worst': patient.fractal_dimension_worst
    }
    
    try:
        preprocessed_data = preprocess(patient_data)
        classification_result = dummy_classification(preprocessed_data)
        return jsonify(classification_result), 200
    except Exception as e:
        return jsonify({'error': f'Error during classification: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True) 