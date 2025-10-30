FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY nfl-backend-server.py .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "nfl-backend-server:app"]
