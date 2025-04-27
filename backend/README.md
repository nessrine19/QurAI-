# Cancer Classification API

A Flask-based REST API that helps care specialists classify whether a person has cancer based on patient data. The API provides endpoints for managing care specialists, uploading patient data, and getting cancer classification predictions.

## Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- Poetry (Python package manager)

## Project Structure

```
backend/
├── app.py                 # Main Flask application
├── docker-compose.yml     # Docker configuration for PostgreSQL
├── pyproject.toml        # Poetry dependency configuration
├── .env                  # Environment variables
├── migrations/           # Database migrations
└── README.md            # This file
```

## Setup Instructions

1. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Clone the Repository and Navigate to Backend**
   ```bash
   cd backend
   ```

3. **Activate Poetry Env**
  ```bash
  poetry env activate
  ```

4. **Install Dependencies**
   ```bash
   poetry install
   ```

5. **Start PostgreSQL Database**
   ```bash
   docker-compose up -d
   ```
   Verify the database is running:
   ```bash
   docker ps
   ```
   You should see a container named `backend-db-1` running.

6. **Initialize the Database**
   ```bash
   poetry run flask db upgrade
   ```

7. **Run the Application**
   ```bash
   poetry run flask run
   ```
   The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Create Care Specialist
- **Endpoint**: `POST /api/care-specialist`
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
      "name": "John Doe",
      "email": "john@example.com"
  }
  ```
- **Response**:
  ```json
  {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
  }
  ```

### 2. Upload Patient Data
- **Endpoint**: `POST /api/upload-patients/<specialist_id>`
- **Content-Type**: `multipart/form-data`
- **Parameters**:
  - `file`: CSV file containing patient data
- **CSV Format**:
  ```
  id,diagnosis,radius_mean,texture_mean,perimeter_mean,area_mean,smoothness_mean,compactness_mean,concavity_mean,concave points_mean,symmetry_mean,fractal_dimension_mean,radius_se,texture_se,perimeter_se,area_se,smoothness_se,compactness_se,concavity_se,concave points_se,symmetry_se,fractal_dimension_se,radius_worst,texture_worst,perimeter_worst,area_worst,smoothness_worst,compactness_worst,concavity_worst,concave points_worst,symmetry_worst,fractal_dimension_worst
  ```
- **Response**:
  ```json
  {
      "message": "Patients uploaded successfully"
  }
  ```

### 3. Get Patient Data
- **Endpoint**: `GET /api/patient/<patient_id>`
- **Response**: All patient data fields

### 4. Get Care Specialist Data
- **Endpoint**: `GET /api/care-specialist/<specialist_id>`
- **Response**:
  ```json
  {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "patient_ids": [1, 2, 3]
  }
  ```

### 5. Classify Patient
- **Endpoint**: `GET /api/classify/<patient_id>`
- **Response**:
  ```json
  {
      "malignant": 0.7,
      "benign": 0.3
  }
  ```

## Data Requirements

### Patient Data CSV Format
The CSV file for uploading patient data must contain the following columns:
- id (unique identifier)
- diagnosis
- radius_mean
- texture_mean
- perimeter_mean
- area_mean
- smoothness_mean
- compactness_mean
- concavity_mean
- concave points_mean
- symmetry_mean
- fractal_dimension_mean
- radius_se
- texture_se
- perimeter_se
- area_se
- smoothness_se
- compactness_se
- concavity_se
- concave points_se
- symmetry_se
- fractal_dimension_se
- radius_worst
- texture_worst
- perimeter_worst
- area_worst
- smoothness_worst
- compactness_worst
- concavity_worst
- concave points_worst
- symmetry_worst
- fractal_dimension_worst

### Classification Model
The API uses a pre-trained model for classification. The model requires:
- A `scaler.pkl` file in the root directory containing a fitted StandardScaler
- The scaler should be trained on the following features:
  - radius_se
  - radius_worst
  - area_worst
  - concave points_mean

## Error Handling
The API includes comprehensive error handling for:
- Invalid CSV format
- Missing required columns
- Duplicate patient IDs
- Database connection issues
- Invalid care specialist or patient IDs

## Development Notes

### Database Management
- To reset the database:
  ```bash
  docker-compose down -v
  docker-compose up -d
  poetry run flask db upgrade
  ```

### Environment Variables
The following environment variables can be configured in `.env`:
- `FLASK_APP`: Set to `app.py`
- `FLASK_ENV`: Set to `development` or `production`
- `DATABASE_URL`: PostgreSQL connection string

## Security Considerations
- The API currently doesn't implement authentication
- For production use, consider adding:
  - API authentication
  - Rate limiting
  - Input validation
  - HTTPS
  - Secure headers 