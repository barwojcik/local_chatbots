## Use Python 3.10 as the base image
FROM python:3.10-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory in container
WORKDIR /app

# Install PyTorch with CUDA support and other dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app .

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["flask", "--app", "app.py", "run", "--host=0.0.0.0"]
