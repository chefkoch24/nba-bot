FROM public.ecr.aws/lambda/python:3.10 as stage

# Install Git
RUN yum install -y git

COPY requirements.txt ./

COPY extractor.py ./

COPY utils.py ./

COPY rag.py ./

COPY generator.py ./

COPY send_email.py ./

COPY daily_generate_function.py ./

RUN python3.10 -m pip install -r requirements.txt -t .

