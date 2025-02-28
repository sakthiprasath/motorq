# Use an official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim as base

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Check if the requirements.txt file is copied correctly
RUN ls -l /app/requirements.txt

# Install any dependencies
RUN pip install --upgrade pip setuptools
RUN pip install  -r requirements.txt --no-cache-dir

# # Copy the contents of the local src directory to the working directory
# COPY . .

COPY src /app
RUN mkdir /app/db
COPY db /app/db
COPY run_with_gunicorn.sh /app
ENV PYTHONPATH /app
RUN mkdir /app/configs
COPY configs/ /app/configs/
# Command to run when starting the container
RUN chmod +x /app/run_with_gunicorn.sh
CMD [ "/app/run_with_gunicorn.sh" ]
