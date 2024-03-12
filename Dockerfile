# Start from the python image
FROM python:3.11-slim

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# We copy the requirements file
COPY ./requirements.txt /app/requirements.txt

# We upgrade pip
RUN pip install --upgrade pip

# We install the dependancies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the source code into the container 
COPY . /app

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]