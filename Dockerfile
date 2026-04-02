# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 7860

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Create a non-root user and switch to it
# Hugging Face Spaces uses user 1000
RUN useradd -m -u 1000 user
RUN chown -R user:user /app
USER user

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/static

# Expose the port Hugging Face expects
EXPOSE 7860

# Run the application
CMD ["./start.sh"]
