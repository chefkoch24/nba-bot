FROM public.ecr.aws/lambda/python:3.10 as stage

COPY requirements.txt ./

COPY scrape.py ./

COPY extract_data.py ./

COPY utils.py ./

COPY generate.py ./

COPY rag.py ./

COPY publish.py ./

COPY generator.py ./

COPY send_email.py ./

RUN python3.10 -m pip install -r requirements.txt -t .

