# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create uploads and data directories for file storage and database
RUN mkdir -p /app/uploads /app/data

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "buckets:app", "--host", "0.0.0.0", "--port", "8000"]
