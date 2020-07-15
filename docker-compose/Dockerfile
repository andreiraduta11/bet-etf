# Use an official Python run time as an image.
FROM python:latest

# Set the working directory. Create the directory if it does not exist.
WORKDIR /bet-etf/docker-compose

# Add requirements.txt before rest of the directory for caching.
COPY requirements.txt /bet-etf/docker-compose

# Install any needed packages specified in requirements.txt.
RUN pip3 install -r requirements.txt

# Copy the rest of the files from the current directory.
COPY . /bet-etf/docker-compose/

CMD ["python3", "application.py"]
