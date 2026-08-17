# main.py

from app import create_app
from dotenv import load_dotenv
import os

load_dotenv()

FLASK_ENV = os.getenv("FLASK_ENV", "development")
PORT = int(os.getenv("PORT", 5000))

app = create_app()

if __name__ == "__main__":
    # If in development, explicitly enable reload engines
    is_debug = FLASK_ENV == "development"
    app.run(debug=is_debug, use_reloader=is_debug, port=PORT)
