FROM python:3.10-slim

# set the working directory
WORKDIR /usr/src/app

# install dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the src to the folder
COPY . . 

# keep container running
ENTRYPOINT ["tail", "-f", "/dev/null"]