FROM ubuntu:bionic

# Install Python
RUN apt-get update && apt-get install -y python3.7 && apt-get install -y curl
RUN curl -O https://bootstrap.pypa.io/get-pip.py
RUN apt-get install -y python3-pip
RUN apt-get install -y python3-distutils
RUN python3.7 get-pip.py
RUN python3.7 -m pip install -U setuptools

# 2. Install WebKit dependencies
RUN apt-get install -y libwoff1 \
                       libopus0 \
                       libwebp6 \
                       libwebpdemux2 \
                       libenchant1c2a \
                       libgudev-1.0-0 \
                       libsecret-1-0 \
                       libhyphen0 \
                       libgdk-pixbuf2.0-0 \
                       libegl1 \
                       libnotify4 \
                       libxslt1.1 \
                       libevent-2.1-6 \
                       libgles2 \
                       libvpx5

# 3. Install Chromium dependencies
RUN apt-get install -y libnss3 \
                       libxss1 \
                       libasound2

RUN apt-get install -y python3.7-dev

RUN pip install --upgrade pip && \
    python3.7 -m pip install playwright --no-cache-dir && \
    python3.7 -m playwright install

RUN python3.7 -m pip install rq --no-cache-dir
RUN python3.7 -m pip install pymongo --no-cache-dir
RUN python3.7 -m pip install minio --no-cache-dir
RUN python3.7 -m pip install yara-python --no-cache-dir
RUN python3.7 -m pip install dnspython --no-cache-dir

RUN rm -rf /var/lib/apt/lists/*

RUN mkdir /app
COPY worker.py /app/worker.py
RUN mkdir /app/yara
COPY yara/* /app/yara/
WORKDIR /app