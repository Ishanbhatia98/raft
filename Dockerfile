FROM python:3.9-slim as venv

# Install C++ Compiler
RUN apt update && apt -y install g++ libpq-dev

# Build and install python requirements
COPY ./requirements.txt /tmp/
RUN pip install wheel && pip install -r /tmp/requirements.txt

# Install runtime dependencies
RUN apt -y install --no-install-recommends libmagickwand-dev ghostscript inotify-tools

RUN apt-get update && apt-get install -y imagemagick
# RUN apt-get update && apt-get install -y ghostscript
RUN apt-get update && apt-get install -y poppler-utils 

# RUN apt-get update && apt-get install -y postgresql-client && apt-get clean
# Needed for writing locally
RUN mkdir /scratch

# Copy app source
COPY ./src /app

# Remaining setup
COPY start.sh start.sh
RUN chmod +x /start.sh

WORKDIR /app
ENV PYTHONPATH=/
EXPOSE 80



CMD ["/start.sh"]
