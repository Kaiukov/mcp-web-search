FROM python:3.10

WORKDIR /app
COPY ./app ./app
COPY requirements.txt .

# Install uv and dependencies
RUN python -m pip install uv && \
    uv pip install --system -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
