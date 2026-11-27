FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
# -u : logs affichés immédiatement dans `docker compose logs`
CMD ["python", "-u", "app.py"]
