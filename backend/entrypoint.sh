#!/bin/bash

echo Starting backend.

exec gunicorn --log-level info\
     -w 1\
     -k uvicorn.workers.UvicornWorker\
     --keep-alive 60\
     --timeout 60\
     --log-file=-\
     app.api:app -b 0.0.0.0:8000