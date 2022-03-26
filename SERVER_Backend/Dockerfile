################################################################
# IMPORTANT:
# WHEN BUILDING DOCKER FOR LIGHTSAIL ON LOCALMACHINE, RUN:
# docker buildx build --platform=linux/amd64 -t <image-name> .
################################################################

FROM python:3.8-slim

EXPOSE 3000/tcp

COPY PythonFiles/ .

RUN pip install -r requirements.txt

CMD ["python", "./api.py"]


