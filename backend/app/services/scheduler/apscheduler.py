# app/services/scheduler/apscheduler.py

import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import os

BACKEND_URL = os.getenv("BACKEND_URL")
is_production = os.getenv("FLASK_ENV") == "production"

def continuous_ping():
    local_tz = ZoneInfo("Africa/Lagos")
    local_time = datetime.now(local_tz).time()

    formatted_time = str(local_time).split(".")[0]

    url = f"{BACKEND_URL}/api/v1/health/me"

    if not is_production:
        print(f"⚠️ Skipping ping in non-production environment at {formatted_time}")
        return
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "OK":
                print(
                    f"✅ Ping successful at {formatted_time}: {data.get('code')}"
                )
        else:
            print(
                f"⚠️ Ping returned {response.status_code} at {formatted_time}"
            )
    except Exception as e:
        print(f"❌ Ping failed at {formatted_time}: {e}")