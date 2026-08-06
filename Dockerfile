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

FROM denoland/deno:alpine-2.9.4@sha256:13851184d6705150b8b230c5377f26c3bd182865d28700bb72bc0b2c271b504a

ARG APP_VERSION=0.1.1
ARG APP_BUILD_SHA=dev
ARG APP_BUILD_DATE=unknown

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
      ca-certificates curl lame-libs libstdc++ openssl opus python3 py3-pip \
      rtmpdump su-exec zlib \
    && addgroup -S -g 10001 pulliku \
    && adduser -S -D -H -u 10001 -G pulliku pulliku \
    && python3 -m venv /opt/venv \
    && pip install --no-cache-dir -r requirements.txt
COPY --from=atomicparsley-build /build/AtomicParsley /usr/local/bin/AtomicParsley
COPY --from=ffmpeg-build /opt/ffmpeg /opt/ffmpeg

COPY app ./app
COPY docker-entrypoint.sh /usr/local/bin/pulliku-entrypoint

RUN mkdir -p /data /downloads /run/secrets \
    && chown -R pulliku:pulliku /app /data /downloads /run/secrets \
    && chmod 755 /usr/local/bin/pulliku-entrypoint

USER root
EXPOSE 8080
VOLUME ["/data", "/downloads"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://localhost:8080/healthz || exit 1

ENTRYPOINT ["/tini", "--", "/usr/local/bin/pulliku-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
