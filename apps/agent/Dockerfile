FROM python:3.14-slim
WORKDIR /app
COPY server.py ./
ENV AGENT_PORT=8090
EXPOSE 8090
CMD ["python", "server.py"]
