FROM python:3.11-slim
WORKDIR /app
COPY main.py /app
RUN pip install python-telegram-bot==20.7
ENV BOT_TOKEN=your_token_here
ENV DB_PATH=/data/data.db
VOLUME ["/data"]
CMD ["python", "main.py"]