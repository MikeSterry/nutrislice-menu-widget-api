"""Run shim for Echo Park Elementary Menu API.

Allows:
  python run.py

This ensures the app package is imported with a proper package context,
so relative imports inside app/ work correctly.
"""

import os
from app.main import app

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("FLASK_ENV", "production").lower() == "development"
    app.run(host=host, port=port, debug=debug)
