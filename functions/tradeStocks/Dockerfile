FROM public.ecr.aws/lambda/python:3.9

RUN pip install boto3 pandas python-dotenv requests

ARG ENV_FILE=".env"

COPY ${ENV_FILE} ${LAMBDA_TASK_ROOT}

COPY tradeStocks.py ./
CMD [ "tradeStocks.handler" ]
