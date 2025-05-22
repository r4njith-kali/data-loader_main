FROM python:3.10-slim

# Expose the application to port 6666
EXPOSE 6666


# Add build-time ARG
# ARG START_DATE="2024-01-01"

# Assign ARG to environment variables (available during runtime)
# ENV START_DATE_ENV=${START_DATE}


# Install PostgreSQL development libraries
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy the application code and CA certificate
COPY . /app

# Set the working directory
WORKDIR /app

# Create the directory for the volume mount point
RUN mkdir -p /M13/data_pipeline

# Update the package list, install necessary packages, and update CA certificates
RUN apt-get update
RUN apt-get install -y ca-certificates
RUN update-ca-certificates


# Install tools
RUN apt-get install -y openssh-client vim-tiny

# Upgrade pip and configure it to use the custom CA certificate
RUN pip install --upgrade pip

# Install the Python dependencies
RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt

# Set environment variables
ENV PYTHONUNBUFFERED=0

# Run main.py when the container launches
CMD ["python", "main.py"]