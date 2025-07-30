# UWS Buckets API - Docker Setup

This FastAPI application provides file upload, download, and management functionality with a SQLite database backend.

## Files Structure

```
├── buckets.py              # Main FastAPI application
├── DB/
│   ├── __init__.py
│   └── db.py              # Database models and configuration
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Docker Compose configuration
├── .dockerignore          # Files to ignore during Docker build
└── README.md              # This file
```

## Building and Running with Docker

### Option 1: Using Docker directly

1. **Build the Docker image:**

   ```bash
   docker build -t buckets-api .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/buckets.db:/app/buckets.db buckets-api
   ```

### Option 2: Using Docker Compose (Recommended)

1. **Build and run:**

   ```bash
   docker-compose up --build
   ```

2. **Run in detached mode:**

   ```bash
   docker-compose up -d --build
   ```

3. **Stop the services:**
   ```bash
   docker-compose down
   ```

## API Endpoints

- `GET /` - Welcome message
- `POST /upload` - Upload a file (requires user_id, bucket, file, and X-Signature header)
- `GET /files` - List all uploaded files
- `GET /download/{file_id}` - Download a file by ID
- `DELETE /delete/{file_id}` - Delete a file by ID

## Accessing the API

Once running, the API will be available at:

- http://localhost:8000
- API documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Environment Variables

- `DATABASE_URL` - Database connection string (defaults to SQLite)

## Authentication

The upload endpoint requires an `X-Signature` header with the value `mysecretkey123` (you should change this in production).

## Data Persistence

- Uploaded files are stored in the `uploads/` directory
- Database is persisted as `buckets.db` SQLite file
- Both are mounted as volumes to persist data between container restarts
