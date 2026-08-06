#!/bin/sh
set -eu

uid="${PULLIKU_UID:-10001}"
gid="${PULLIKU_GID:-10001}"

if [ "$(id -u)" = "0" ]; then
  chown -R "$uid:$gid" /data /downloads
  exec su-exec "$uid:$gid" "$@"
fi

exec "$@"
