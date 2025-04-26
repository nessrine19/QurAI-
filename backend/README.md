# QurAI Backend

This is the backend service for the QurAI application, a cancer treatment optimization and radiotherapy planning system.

## Features

- Patient data management
- Care specialist management
- Treatment cycle tracking
- Patient classification and outcome prediction
- RESTful API endpoints

## Prerequisites

### For macOS:
1. Python 3.9 or higher
2. Poetry (Python package manager)
3. PostgreSQL 14 or higher
4. Homebrew (for macOS package management)

### For Windows:
1. Python 3.9 or higher
2. Poetry (Python package manager)
3. PostgreSQL 14 or higher
4. Git Bash (recommended for command line operations)

## Installation

### macOS Setup

1. Install Python:
```bash
brew install python@3.9
```

2. Install Poetry:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

3. Install PostgreSQL:
```bash
brew install postgresql@14
brew services start postgresql@14
```

4. Create PostgreSQL user and database:
```bash
createuser -s postgres
createdb qurai_db
createdb qurai_test_db
```

### Windows Setup

1. Install Python:
   - Download Python 3.9 or higher from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. Install Poetry:
   - Open PowerShell as Administrator
   - Run:
   ```powershell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
   ```

3. Install PostgreSQL:
   - Download PostgreSQL 14 from [postgresql.org](https://www.postgresql.org/download/windows/)
   - During installation:
     - Set password for postgres user
     - Keep the default port (5432)
     - Complete the installation

4. Create databases:
   - Open pgAdmin 4 (installed with PostgreSQL)
   - Connect to your server
   - Right-click on "Databases" → Create → Database
   - Create two databases: `qurai_db` and `qurai_test_db`

## Project Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/QurAI-.git
cd QurAI-/backend
```

2. Install dependencies:
```bash
poetry install
```

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the following variables:
     ```
     DATABASE_URL=postgresql://postgres:your_password@localhost:5432/qurai_db
     TEST_DATABASE_URL=postgresql://postgres:your_password@localhost:5432/qurai_test_db
     ```

   For Windows, you can create the `.env` file using Notepad or any text editor.

4. Initialize the database:
```bash
# Run migrations
poetry run alembic upgrade head
```

## Running the Application

### Development Server

```bash
# Start the development server
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:
```bash
poetry run pytest tests/ -v
```

## API Endpoints

### Root
- `GET /`: Welcome message
- `GET /health`: Health check

### Care Specialists
- `POST /care-specialists/`: Create a new care specialist
- `GET /care-specialists/{specialist_id}/patients`: Get patients for a specialist

### Patients
- `GET /patients/{patient_id}`: Get patient details
- `POST /upload/patients`: Upload patient data via CSV
- `GET /patients/{patient_id}/classify`: Classify patient treatment outcome

## Database Schema

### Patients Table
- `patient_id`: Primary key
- `first_name`: Patient's first name
- `last_name`: Patient's last name
- `date_of_birth`: Patient's date of birth
- `gender`: Patient's gender
- `diagnosis`: Medical diagnosis
- `tumor_location`: Location of the tumor
- `tumor_stage`: Stage of the tumor
- `treatment_plan`: Treatment plan details
- `notes`: Additional notes
- `specialist_id`: ID of the assigned care specialist
- `biomarkers`: Biomarker information
- `treatment_cycle`: Current treatment cycle number
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

### Care Specialists Table
- `specialist_id`: Primary key
- `first_name`: Specialist's first name
- `last_name`: Specialist's last name
- `email`: Specialist's email address
- `specialization`: Area of medical specialization
- `created_at`: Record creation timestamp
- `updated_at`: Record update timestamp

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 