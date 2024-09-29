# Use the latest Ubuntu image
FROM ubuntu:latest

# Set environment variable to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Update and install necessary dependencies
RUN apt-get update && \
    apt-get install -y \
    python3 \
    python3-pip \
    bluez \
    libglib2.0-dev \
    sudo && \
    apt-get clean

# Copy the Python script into the container
COPY app/sensors_exporter.py /usr/src/app/sensors_exporter.py

# Install Python dependencies
RUN pip3 install prometheus_client lywsd03mmc --break-system-packages

# Set the working directory
WORKDIR /usr/src/app

# Default command to run the service script
CMD ["python3", "sensors_exporter.py", "--config", "devices.json", "--conn-frequency", "60"]
