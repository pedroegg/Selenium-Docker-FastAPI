FROM python:3.11.13

ENV CHROME_BIN="/usr/bin/chromium"
ENV CHROMEDRIVER_PATH="/usr/bin/chromedriver"

ENV JAVA_HOME="/opt/java"
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV BROWSERMOB_PATH="/browsermob-proxy/bin/browsermob-proxy"

RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 ca-certificates \
    chromium-driver chromium && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/java && \
    wget -q https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u402-b06/OpenJDK8U-jre_x64_linux_hotspot_8u402b06.tar.gz -O /tmp/java.tar.gz && \
    tar -xzf /tmp/java.tar.gz -C /opt/java --strip-components=1 && \
    rm /tmp/java.tar.gz

RUN java -version

WORKDIR /browsermob-proxy
COPY browsermob-proxy/ .

WORKDIR /app
COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]