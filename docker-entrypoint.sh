#!/bin/sh
set -eu

uid="${PULLIKU_UID:-10001}"
gid="${PULLIKU_GID:-10001}"

if [ "$(id -u)" = "0" ]; then
  if ! chown -R "$uid:$gid" /data /downloads 2>/dev/null; then
    echo "Pulliku could not change bind-mount ownership; checking existing permissions." >&2
  fi
  if ! su-exec "$uid:$gid" sh -c 'test -w /data && test -w /downloads'; then
    echo "Pulliku requires /data and /downloads to be writable by UID:GID ${uid}:${gid}." >&2
    exit 1
  fi
  exec su-exec "$uid:$gid" "$@"
fi

exec "$@"
