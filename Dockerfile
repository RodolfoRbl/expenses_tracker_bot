FROM public.ecr.aws/lambda/python:3.11

RUN yum install -y gcc rust cargo zip
RUN mkdir /mnt/python

WORKDIR /opt/python

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt --target /mnt/python/
RUN cd /mnt && zip -r my-layer.zip python/

ENTRYPOINT ["/bin/bash"]
