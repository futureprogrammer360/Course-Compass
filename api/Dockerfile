FROM public.ecr.aws/lambda/python:3.12

WORKDIR ${LAMBDA_TASK_ROOT}

ENV PYTHONDONTWRITEBYTECODE=1

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

COPY ./*.py .

RUN chmod -R 755 .

EXPOSE 8080

CMD ["api.handler"]
