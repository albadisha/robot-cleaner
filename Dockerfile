# Use Python 3.12 Alpine as the base image
FROM python:3.12-alpine

# Install system dependencies and update
RUN apk update && \
    apk add --no-cache \
        build-base \
        libffi-dev \
        libpq-dev

# Set the working directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project files and dependencies
COPY src/ .

# Install project dependencies
RUN poetry install --no-root --no-interaction --no-ansi

EXPOSE 5000

# Set the starting script
CMD ["/app/entrypoint.sh"]