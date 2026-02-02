# Using the official Python image (slim version for a smaller size)
FROM python:3.14.2-slim

# Image metadata
LABEL maintainer="t.salakhov@innopolis.university"
LABEL description="DevOps Info Service"
LABEL version="1.0.0"

# Install the working directory
WORKDIR /app

# Creating an unprivileged user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only requirements.txt first (for caching layers)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app.py .

# Changing the file owner to appuser
RUN chown -R appuser:appuser /app

# Switching to an unprivileged user
USER appuser

# Documenting the port used
EXPOSE 5000

# Setting the default environment variables
ENV HOST=0.0.0.0
ENV PORT=5000
ENV DEBUG=False

# The application launch command
CMD ["python", "app.py"]