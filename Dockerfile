FROM python:3.10-slim
RUN pip install --upgrade pip
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . . 
RUN mkdir -p data config
CMD ["python", "run_service.py"]