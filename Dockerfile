# Use the official Python image.
# It automatically uses the latest version of Python.
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable
ENV FLASK_APP=app.py

# Set a build-time argument
ARG OPENAI_API_KEY

# Use the argument to set an environment variable
ENV OPENAI_API_KEY=$OPENAI_API_KEY

# Command to run the Flask app and enable multithreading
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000", "--with-threads"]
