FROM python:3.10-slim

# set the working directory
WORKDIR /usr/src/app

# install dependencies
COPY ./requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# copy the src to the folder
COPY . . 
WORKDIR /usr/src/app/src
# keep container running
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]