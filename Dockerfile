# Use the base image
FROM python:3.8

# Set the timezone
ENV TZ "Asia/Shanghai"

# Set the encoding
ENV LANG C.UTF-8

# Set the working directory
WORKDIR /code

# Copy the local project files to the /code directory in the container
COPY . /code

# Install venv and requirements
RUN python3.8 -m venv venv

# Activate the virtual environment
ENV PATH=/code/venv/bin:/code:$PATH

# Upgrade pip
RUN pip3.8 install --upgrade pip

# Install the dependencies from requirements.txt
RUN pip3.8 install -r requirements.txt

# Run the test command
CMD ["python3.8", "main.py"]
