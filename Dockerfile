# Docker container based on raspbian OS

FROM --platform=amd64 python:3.12 AS uv
WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN pip install --no-cache-dir uv==0.9.11

RUN uv export --no-dev --format requirements.txt -o requirements.txt --no-hashes
RUN sed -i 's/-e .//g' requirements.txt

FROM --platform=linux/arm/v6 balenalib/rpi-raspbian:buster AS final

RUN sed -i 's|http://archive.raspbian.org/raspbian|http://legacy.raspbian.org/raspbian|g' /etc/apt/sources.list

RUN apt-get update --allow-releaseinfo-change && apt-get install -y \
    build-essential wget libssl-dev zlib1g-dev \
    libncurses5-dev libtinfo-dev libgdbm-dev libnss3-dev \
    libreadline-dev libffi-dev libsqlite3-dev tk-dev \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /build

RUN wget https://www.python.org/ftp/python/3.12.12/Python-3.12.12.tgz && \
    tar -xvzf Python-3.12.12.tgz && \
    cd Python-3.12.12 && \
    ./configure --enable-optimizations --prefix=/opt/python312 --with-ensurepip=install && \
    make -j $(nproc) && \
    make install

ENV PATH="/opt/python312/bin:$PATH"

COPY --from=uv /app/requirements.txt /build/

RUN /opt/python312/bin/python3 -m pip install --no-cache-dir -r requirements.txt

COPY deployment/docker-entry.sh /entry.sh
RUN chmod +x /entry.sh
ENTRYPOINT ["/entry.sh"]
