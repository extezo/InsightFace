#!/bin/bash
echo Starting backend using "$NUM_WORKERS" workers.

exec gunicorn --log-level debug\
     -k uvicorn.workers.UvicornWorker\
     -w "$NUM_WORKERS"\
     --keep-alive 60\
     --timeout 60\
     --log-file=-\
     backend_api:app -b 0.0.0.0:"$BACKEND_INNER_PORT"