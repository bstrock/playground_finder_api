FROM python:3.9.6-slim-buster

WORKDIR .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ENV PYTHONPATH .
copy . .
WORKDIR .
# CMD ["python3", "./utils/test.py"]
# CMD ["uvicorn", "api.api:app", "--host", "0.0.0.0", "--port=${PORT:-5000}"]
