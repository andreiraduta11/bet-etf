# Use an official Python runtime as an image.
FROM python:latest

# Set the working directory. Create the directory if it does not exist.
WORKDIR /collector

# Add requirements.txt before rest of the directory for caching.
COPY requirements.txt /collector/

# Install any needed packages specified in requirements.txt.
RUN pip3 install -r requirements.txt

# Copy the rest of the files in the working directory and run the application.
COPY . /collector/

CMD ["python3", "collector.py"]
