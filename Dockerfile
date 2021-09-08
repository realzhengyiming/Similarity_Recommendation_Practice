# set base image (host OS)
FROM python:3.8-slim-buster

# set the working directory in the container
WORKDIR /

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt -i "https://pypi.tuna.tsinghua.edu.cn/simple"

# copy the content of the local src directory to the working directory
COPY . /

EXPOSE 5000

## command to run on container start
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "5000"]
