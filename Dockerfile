ARG ATOMICPARSLEY_REPO=https://github.com/wez/atomicparsley.git
ARG ATOMICPARSLEY_REF=1ed9031faaea5c75f88b2135d04b29ef24766788
ARG FFMPEG_REPO=https://github.com/FFmpeg/FFmpeg.git
ARG FFMPEG_REF=38b88335f99e76ed89ff3c93f877fdefce736c13

FROM alpine:3.23@sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40 AS atomicparsley-build
ARG ATOMICPARSLEY_REPO
ARG ATOMICPARSLEY_REF
RUN apk add --no-cache cmake g++ git linux-headers make zlib-dev \
    && git init /src \
    && git -C /src remote add origin "${ATOMICPARSLEY_REPO}" \
    && git -C /src fetch --depth 1 origin "${ATOMICPARSLEY_REF}" \
    && git -C /src checkout --detach FETCH_HEAD \
    && test "$(git -C /src rev-parse HEAD)" = "${ATOMICPARSLEY_REF}" \
    && cmake -S /src -B /build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /build --parallel

FROM alpine:3.23@sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40 AS ffmpeg-build
ARG FFMPEG_REPO
ARG FFMPEG_REF
RUN apk add --no-cache \
      build-base git lame-dev nasm openssl-dev opus-dev pkgconf zlib-dev \
    && git init /src \
    && git -C /src remote add origin "${FFMPEG_REPO}" \
    && git -C /src fetch --depth 1 origin "${FFMPEG_REF}" \
    && git -C /src checkout --detach FETCH_HEAD \
    && test "$(git -C /src rev-parse HEAD)" = "${FFMPEG_REF}" \
    && cd /src \
    && ./configure \
      --prefix=/opt/ffmpeg \
      --disable-autodetect \
      --disable-debug \
      --disable-doc \
      --disable-static \
      --enable-gpl \
      --enable-libmp3lame \
      --enable-libopus \
      --enable-openssl \
      --enable-pic \
      --enable-shared \
      --enable-version3 \
      --enable-zlib \
    && make -C /src -j"$(getconf _NPROCESSORS_ONLN)" \
    && make -C /src install \
    && LD_LIBRARY_PATH=/opt/ffmpeg/lib /opt/ffmpeg/bin/ffmpeg -version \
    && LD_LIBRARY_PATH=/opt/ffmpeg/lib /opt/ffmpeg/bin/ffprobe -version

FROM denoland/deno:alpine-2.8.3@sha256:9eb3b9b8bd4f821de57239792f76f6a3bef29a7bfbd486b801cbf34fc2c32797 AS deno-runtime

FROM alpine:3.23@sha256:fd791d74b68913cbb027c6546007b3f0d3bc45125f797758156952bc2d6daf40 AS runtime-base

ARG VERSION=0.1.1
ARG GIT_SHA=dev
ARG BUILD_DATE=unknown
ARG APP_VERSION=${VERSION}
ARG APP_BUILD_SHA=${GIT_SHA}
ARG APP_BUILD_DATE=${BUILD_DATE}

LABEL org.opencontainers.image.title="Pulliku" \
      org.opencontainers.image.description="Controlled self-hosted media downloads through yt-dlp" \
      org.opencontainers.image.licenses="NOASSERTION" \
      org.opencontainers.image.source="https://github.com/MaroIshiku/pulliku" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${APP_BUILD_SHA}" \
      org.opencontainers.image.created="${APP_BUILD_DATE}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ISHIKU_DATA_DIR=/data \
    DOWNLOAD_DIR=/downloads \
    APP_VERSION=${APP_VERSION} \
    APP_BUILD_SHA=${APP_BUILD_SHA} \
    APP_BUILD_DATE=${APP_BUILD_DATE} \
    DENO_DIR=/tmp/deno \
    LD_LIBRARY_PATH=/opt/ffmpeg/lib \
    PATH=/opt/ffmpeg/bin:/opt/venv/bin:${PATH}

WORKDIR /app

COPY requirements.txt .
RUN apk upgrade --no-cache \
    && apk add --no-cache \
      ca-certificates lame-libs libstdc++ openssl opus python3 py3-pip \
      rtmpdump su-exec tini zlib \
    && addgroup -S -g 10001 pulliku \
    && adduser -S -D -H -u 10001 -G pulliku pulliku \
    && python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r requirements.txt
COPY --from=atomicparsley-build /build/AtomicParsley /usr/local/bin/AtomicParsley
COPY --from=ffmpeg-build /opt/ffmpeg /opt/ffmpeg
COPY --from=deno-runtime /bin/deno /usr/local/bin/deno
COPY --from=deno-runtime /usr/local/lib/glibc /usr/local/lib/glibc

COPY app ./app
COPY docker-entrypoint.sh /usr/local/bin/pulliku-entrypoint

RUN mkdir -p /data /downloads /run/secrets \
    && mkdir -p /lib64 \
    && ln -sf /usr/local/lib/glibc/ld-linux-x86-64.so.2 /lib64/ld-linux-x86-64.so.2 \
    && chown -R pulliku:pulliku /app /data /downloads /run/secrets \
    && chmod 755 /usr/local/bin/pulliku-entrypoint

USER root
EXPOSE 8080
VOLUME ["/data", "/downloads"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/readyz || exit 1

ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/pulliku-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

FROM runtime-base AS test
USER root
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY tests ./tests
RUN python -m unittest discover -s tests -v

FROM runtime-base AS final
RUN pip uninstall -y pip setuptools wheel \
    && apk del py3-pip
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/readyz || exit 1
