from sqlalchemy import text
from .database import engine, Base
from .models.patient import Patient, CareSpecialist

def init_db():
    """Initialize the database by creating all tables."""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise

def drop_all_tables():
    """Drop all tables in the database."""
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("All tables dropped successfully")
    except Exception as e:
        print(f"Error dropping tables: {e}")
        raise

def check_tables_exist():
    """Check if the required tables exist in the database."""
    try:
        with engine.connect() as conn:
            # Check if care_specialists table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'care_specialists'
                );
            """))
            care_specialists_exists = result.scalar()

            # Check if patients table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'patients'
                );
            """))
            patients_exists = result.scalar()

            return care_specialists_exists and patients_exists
    except Exception as e:
        print(f"Error checking tables: {e}")
        return False 