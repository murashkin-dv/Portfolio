FROM python:3.11.3-slim-buster

# set environment variables
# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

# set project directory
ENV APP=/usr/src/app
ADD . $APP
# set working directory
WORKDIR $APP

# install dependencies
RUN pip install --upgrade pip
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    python3-dev \
    nginx \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt $APP/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy project
COPY . $APP

CMD ["uvicorn", "main.app:create_app", "--host", "0.0.0.0", "--port", "5000",\
     "--reload", "--factory", "--uds", "/run/uvicorn.sock"]
