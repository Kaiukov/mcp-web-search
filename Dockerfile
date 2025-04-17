FROM python:3.10

WORKDIR /app
# Add config directory copy
COPY ./app ./app
COPY requirements.txt .

# Install dependencies including python-dotenv
RUN pip install uv && \
    uv pip install --system -r requirements.txt python-dotenv

# Add Python path configuration
ENV PYTHONPATH="${PYTHONPATH}:/app/"

# Change to uvicorn instead of uv run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
