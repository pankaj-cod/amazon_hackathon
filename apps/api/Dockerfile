FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY app ${LAMBDA_TASK_ROOT}/app
COPY demo_cache ${LAMBDA_TASK_ROOT}/demo_cache

ENV CACHE_DIR=/tmp/cache \
    SEED_CACHE_DIR=${LAMBDA_TASK_ROOT}/demo_cache \
    GDAL_CACHEMAX=128

CMD ["app.lambda_handler.handler"]
