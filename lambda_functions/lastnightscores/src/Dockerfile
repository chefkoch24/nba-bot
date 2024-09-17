FROM public.ecr.aws/lambda/python:3.10 as stage

# Hack to install chromium dependencies
RUN yum install -y -q sudo unzip
# Current stable version of Chromium
ENV CHROMIUM_VERSION=1002910
# Install Chromium
COPY install-browser.sh /tmp/

RUN /usr/bin/bash /tmp/install-browser.sh

FROM public.ecr.aws/lambda/python:3.10 as base
COPY chrome-deps.txt /tmp/
RUN yum install -y $(cat /tmp/chrome-deps.txt)
COPY --from=stage /opt/chrome /opt/chrome
COPY --from=stage /opt/chromedriver /opt/chromedriver

# Install git
RUN yum -y install git

COPY requirements.txt ./

COPY scrape.py ./

COPY extractor.py ./

COPY utils.py ./

COPY generate.py ./

COPY rag.py ./

COPY publish.py ./

COPY generator.py ./

COPY send_email.py ./

RUN python3.10 -m pip install -r requirements.txt -t .

