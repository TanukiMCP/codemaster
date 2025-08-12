FROM python:3.11-slim

WORKDIR /app

# Ensure sh is available (required by Smithery)
RUN which sh

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "server.py"] 