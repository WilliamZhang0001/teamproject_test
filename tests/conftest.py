"""
Pytest configuration and shared fixtures for DoE-Assist tests
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from datetime import datetime, timezone

# Import before creating Base
from backend.app.core.db import Base
from backend.app.main import app
from backend.app.models.user import AppUser
from backend.app.models.literature import Literature, ExtractionRecord
from backend.app.models.user_experiment import UserExperimentRecord
from backend.app.core.security import hash_password


# Create in-memory SQLite database for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides = {}
    from backend.app.core.dependencies import get_db
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "user",
        "is_active": True
    }


@pytest.fixture
def sample_user(db_session: Session, sample_user_data: dict):
    """Create a sample user in the database"""
    user = AppUser(
        username=sample_user_data["username"],
        email=sample_user_data["email"],
        password_hash=hash_password(sample_user_data["password"]),
        role=sample_user_data["role"],
        is_active=sample_user_data["is_active"],
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def inactive_user(db_session: Session, sample_user_data: dict):
    """Create an inactive user for testing"""
    user = AppUser(
        username="inactive_user",
        email="inactive@example.com",
        password_hash=hash_password(sample_user_data["password"]),
        role="user",
        is_active=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_literature(db_session: Session):
    """Create sample literature record"""
    literature = Literature(
        doi="10.1000/test.doi",
        title="Test Literature Title",
        authors="Test Author 1, Test Author 2",
        pub_year=2023,
        source="test",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(literature)
    db_session.commit()
    db_session.refresh(literature)
    return literature


@pytest.fixture
def sample_extraction_record(db_session: Session, sample_literature: Literature):
    """Create sample extraction record"""
    record = ExtractionRecord(
        literature_id=sample_literature.id,
        biomolecule_type="protein",
        protein_name="lysozyme",
        property="stability",
        pH=7.0,
        temperature_c=25.0,
        concentration_mg_ml=10.0,
        ionic_strength_mM=150.0,
        additive="NaCl",
        outcome_score=0.85,
        outcome_label="stable",
        confidence=0.9,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture
def sample_experiment_record(db_session: Session, sample_user: AppUser):
    """Create sample experiment record"""
    record = UserExperimentRecord(
        user_id=sample_user.id,
        biomolecule_type="protein",
        biomolecule_name="lysozyme",
        experiment_type="stability",
        input_pH=7.0,
        input_temperature_c=25.0,
        input_concentration_mg_ml=10.0,
        prediction_type="classification",
        prediction_result='{"prediction": "Good", "confidence": 0.85}',
        confidence=0.85,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(record)
    db_session.commit()
    db_session.refresh(record)
    return record


@pytest.fixture
def auth_token(client, sample_user, sample_user_data):
    """Get authentication token for testing"""
    response = client.post(
        "/auth/login",
        json={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    return None


@pytest.fixture
def authenticated_client(client, sample_user, sample_user_data):
    """Create authenticated test client"""
    # First login to get token
    response = client.post(
        "/auth/login",
        json={
            "username": sample_user_data["username"],
            "password": sample_user_data["password"]
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
    return client

