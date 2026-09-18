FROM python:3.11-slim

WORKDIR /app

COPY air_project/server/ /app/server/
COPY air_project/*.py /app/
COPY air_project/*.pt /app/
COPY air_project/*.pkl /app/
COPY air_project/*.csv /app/

RUN pip install --no-cache-dir numpy pandas

EXPOSE 5000

CMD ["python", "server/app.py"]
