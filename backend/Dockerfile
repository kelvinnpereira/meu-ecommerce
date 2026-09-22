# Stage 1: Build a base image with Python and Playwright dependencies
FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# Set the working directory
WORKDIR /app

# Copy requirements files
COPY ./requirements.txt /app/requirements.txt
COPY ./requirements-dev.txt /app/requirements-dev.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy the rest of the application code
COPY . .

EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
