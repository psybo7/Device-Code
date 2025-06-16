FROM python:3.9-slim

WORKDIR /app

RUN mkdir /app/data

COPY . .

RUN apt update && apt install jq sqlite3 libsqlite3-dev -y 

RUN pip install flask requests gunicorn pyjwt

#CMD ["python", "proxy_server.py"]

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "-c", "gunicorn_config.py", "app:app"]
