FROM ubuntu:16.04

ADD requirements.txt setup.py package/
ADD modelforge package/modelforge

RUN apt-get update && \
    apt-get install -y git python3 python3-dev gcc curl && \
    apt-get clean && \
    curl https://bootstrap.pypa.io/get-pip.py | python3 && \
    pip3 install --no-cache-dir -r package/requirements.txt && \
    apt-get remove -y python3-dev gcc curl && \
    apt-get autoremove -y

RUN pip3 install --no-cache-dir ./package && rm -rf package

ENTRYPOINT ["modelforge"]
