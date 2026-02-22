import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruiter.db")
GDEV_API_TOKEN = os.getenv("GDEV_API_TOKEN", "dev-token")
APP_NAME = "Recruiter Pro"
APP_VERSION = "1.0.0"
