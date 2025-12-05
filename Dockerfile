# Use an official Python runtime as a parent image
FROM python:3.10-slim-bookworm

# Ensure image associated witht the correct repo when pushed to the GitHub Container Registry
LABEL org.opencontainers.image.source=https://github.com/gravercentret/kommunale_investeringer_app

# Default values for environment variable used in the image
ENV STREAMLIT_SERVER_PORT=5000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV MAIN_PAGE=webapp/Forside.py

# Note that sqlite urls start with triple slashes
# Thus "sqlite:///data.db"  will use "data.db" in the current WORKDIR (relative)
# and "sqlite:////data/data.db" will use "/data/data.db" in the root of the filesystem (absolute)
ENV DATABASE_URL=sqlite:///data/data.db

# Define expected mount point for database data file
VOLUME /data

# Create a directory for the database and set permissions
RUN mkdir -p /data && chmod -R 755 /data

# Expose the port Streamlit runs on
EXPOSE 5000

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . /app

# Run the Streamlit app
ENTRYPOINT [ "streamlit", "run" ]
CMD ["/app/webapp/Forside.py"]
