FROM python:3.11-slim

WORKDIR /app

# Install git (needed for GitHub fetcher)
RUN apt-get update && apt-get install -y git

# Copy everything FIRST
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]