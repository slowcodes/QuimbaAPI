# Dockerfile

# pull the official docker image
FROM python:3.11.1-slim

# set work directory
WORKDIR /app

# set env variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ensures numpy and other C extensions build properly.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    libffi-dev libssl-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --default-timeout=100 -r requirements.txt -i https://pypi.org/simple

# copy project
COPY . .

# Expose the port on which the application will run
EXPOSE 8000

# Run the FastAPI application using uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "3"]
