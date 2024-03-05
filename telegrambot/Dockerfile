FROM python:3.11-slim

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV PIP_INSTALL="python -m pip --no-cache-dir install --upgrade"

COPY requirements.txt .
RUN $PIP_INSTALL -r requirements.txt

WORKDIR /app
COPY ./api /app/telegrambot/api
COPY ./handlers /app/telegrambot/handlers
COPY ./keyboards /app/telegrambot/keyboards
COPY basic.py /app
RUN echo "" > /app/telegrambot/init.py

ENTRYPOINT ["python"]
CMD ["basic.py"]
