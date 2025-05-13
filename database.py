from db_config import engine, Base
from models import User, Attendance

# Create all tables
Base.metadata.create_all(bind=engine)

print("База данных создана!")
