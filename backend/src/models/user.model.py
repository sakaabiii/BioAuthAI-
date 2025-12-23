import sys
import os

# Add the 'src' directory to sys.path so Python can find 'database.py'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from database import Base  # Import the Base class from database.py
from sqlalchemy import Column, Integer, String, Float, JSON

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_id = Column(String, unique=True, nullable=False)  # Unique user_id
    session_id = Column(String, nullable=False)
    dwell_times = Column(JSON, nullable=True)  # Store dwell_times as JSON
    typing_speed = Column(Float, nullable=True)
    pause_patterns = Column(JSON, nullable=True)  # Store pause_patterns as JSON

    def __repr__(self):
        return f"<User(user_id={self.user_id}, session_id={self.session_id})>"
