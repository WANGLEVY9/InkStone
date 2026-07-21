#!/bin/bash
set -e

echo "Waiting for MySQL to be ready..."
python3 << 'EOF'
import socket
import time
for i in range(30):
    try:
        s = socket.create_connection(("mysql", 3306), timeout=1)
        s.close()
        print("MySQL is ready")
        break
    except:
        print(f"Attempt {i+1}/30: MySQL not ready, retrying...")
        time.sleep(2)
else:
    print("MySQL not available after 30 attempts, continuing anyway...")
EOF

echo "Creating tables from models..."
python3 << 'PYEOF'
from app.core.database import engine
from app.models import Base
Base.metadata.create_all(bind=engine)
print("All tables created successfully")
PYEOF

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
