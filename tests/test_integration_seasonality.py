import unittest
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infra.orm_models import Base
from infra.db import get_db
from local_api.app import app

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_seasonality.db"
# Use a separate engine per test or recreate it? Unittest is easy with setUp/tearDown

class TestSeasonalityAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Override get_db
        def override_get_db():
            try:
                db = cls.TestingSessionLocal()
                yield db
            finally:
                db.close()
        
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)
        
    def setUp(self):
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        
    def tearDown(self):
        # Drop tables
        Base.metadata.drop_all(bind=self.engine)
        
    @classmethod
    def tearDownClass(cls):
        # Remove DB file
        if os.path.exists("./test_seasonality.db"):
            os.remove("./test_seasonality.db")

    def test_create_and_list_event(self):
        # List empty
        response = self.client.get("/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

        # Create Event
        evt_data = {
            "name": "Test Holiday",
            "date": "2025-12-25",
            "factor": 1.5,
            "note": "Testing"
        }
        response = self.client.post("/events/", json=evt_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Test Holiday")
        self.assertEqual(data["factor"], 1.5)
        evt_id = data["id"]
        
        # List again
        response = self.client.get("/events/")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], evt_id)
        
        # Delete
        self.client.delete(f"/events/{evt_id}")
        
    def test_update_event(self):
        # Create
        evt_data = {"name": "Upd Test", "date": "2025-01-01", "factor": 1.0}
        res = self.client.post("/events/", json=evt_data)
        evt_id = res.json()["id"]
        
        # Update
        upd_data = {"name": "Upd Test Modified", "date": "2025-01-02", "factor": 2.0}
        res = self.client.put(f"/events/{evt_id}", json=upd_data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "Upd Test Modified")
        
        # Verify List
        res = self.client.get("/events/")
        self.assertEqual(res.json()[0]["factor"], 2.0)
        
        self.client.delete(f"/events/{evt_id}")

    def test_backtest_endpoint(self):
        response = self.client.post("/backtest/seasonality")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "completed")
        self.assertIn("metrics_before", data)

if __name__ == "__main__":
    unittest.main()
