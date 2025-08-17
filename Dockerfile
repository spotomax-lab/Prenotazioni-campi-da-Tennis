
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV APP_TZ=Europe/Rome OPEN_TIME=08:00 CLOSE_TIME=22:00 ADMIN_PASSWORD=CHANGE_ME
EXPOSE 8000
CMD ["python","app.py"]
