FROM mcr.microsoft.com/playwright/python:v1.40.0-focal

# Create and switch to a new non-root user
RUN useradd -m appuser
USER appuser

WORKDIR /home/appuser/app

# Add user's local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy requirements first to leverage Docker cache
COPY --chown=appuser:appuser ./requirements.txt ./requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

# This is needed by playwright
RUN playwright install chromium

# Copy the rest of the application code
COPY --chown=appuser:appuser . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
