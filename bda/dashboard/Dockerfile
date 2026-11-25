FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard/app.py /app/dashboard_app.py
EXPOSE 8501
CMD ["streamlit", "run", "dashboard_app.py", "--server.address=0.0.0.0"]
