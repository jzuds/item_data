# Use an official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /dashboard

# Install system dependencies for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy app files
COPY requirements.txt .
COPY app.py .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port app
EXPOSE 8050

# Run the app
CMD ["streamlit","run","app.py", "--server.port", "8050"]