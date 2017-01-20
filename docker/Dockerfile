# bring in a base container
FROM ubuntu:16.04

# install ubuntu dependencies
RUN apt-get update && \
    apt-get install -y \
        python2.7 \
        python-pip \
        python-dev \
        build-essential

# install python dependencies
COPY configs/requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt

# aws credentials for boto3
ENV AWS_SHARED_CREDENTIALS_FILE /project/deployer/configs/aws
ENV AWS_PROFILE default

# copy the run script to the container
COPY configs/run.sh /root/run.sh

# run python
ENTRYPOINT ["/root/run.sh"]