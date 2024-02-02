FROM python:3.11-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PIP_INSTALL="python -m pip --no-cache-dir install --upgrade"

COPY requirements.txt .
RUN $PIP_INSTALL -r requirements.txt

WORKDIR /app
COPY . /app

ENTRYPOINT [ "bash" ]
CMD ["entrypoint.sh"]
