# Python 3.9 base image
FROM python:3.9-slim

# Root olarak sistem paketlerini kur
USER root

# Sistem güncellemesi
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    software-properties-common \
    apt-transport-https \
    ca-certificates

# Google Chrome repository ekle
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Google Chrome kurulumu
RUN apt-get update && apt-get install -y \
    google-chrome-stable

# ChromeDriver kurulumu
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/104.0.5112.79/chromedriver_linux64.zip && \
    unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip

# Python paketleri için requirements kopyala
COPY requirements.txt .

# Python paketlerini kur
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . /app
WORKDIR /app

# Port (opsiyonel, Background Worker için gerekli değil)
EXPOSE 8080

# Uygulamayı çalıştır
CMD ["python", "bot.py"]