################################################################
# IMPORTANT:
# WHEN BUILDING DOCKER FOR LIGHTSAIL, RUN:
# docker buildx build --platform=linux/amd64 -t <image-name> .
################################################################

FROM python:3.8-slim

EXPOSE 3000/tcp

WORKDIR /app

COPY PythonFiles/ /app

RUN pip install -r requirements.txt

CMD ["python", "./api.py"]


