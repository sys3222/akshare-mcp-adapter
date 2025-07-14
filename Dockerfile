FROM python:3.9-slim

WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 12001

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "12001"]