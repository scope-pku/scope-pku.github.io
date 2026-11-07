#!/bin/sh
# Build the Hugo site and publish it to tencent-kr behind Cloudflare (lmxu.cc).
#   BASEURL  override the canonical origin (default https://lmxu.cc/)
#   HOST     ssh target (default tencent-kr)
#   ROOT     remote document root (default /var/www/scope-web)
set -eu

BASEURL=${BASEURL:-https://lmxu.cc/}
URLBASE=${BASEURL%/}
HOST=${HOST:-tencent-kr}
ROOT=${ROOT:-/var/www/scope-web}
CHECK_URLS=${CHECK_URLS:-/ /zh/ /research/ /zh/research/ /media/limei-xu-cv.pdf}

cd "$(dirname "$0")/.."

hugo --source site --minify --cleanDestinationDir --baseURL "$BASEURL" --destination public

rsync -a --delete site/public/ "$HOST:/tmp/scope-web-build/"
ssh "$HOST" "sudo -n rsync -a --delete /tmp/scope-web-build/ $ROOT/ \
  && sudo -n chown -R root:root $ROOT \
  && sudo -n find $ROOT -type d -exec chmod 755 {} + \
  && sudo -n find $ROOT -type f -exec chmod 644 {} +"

for path in $CHECK_URLS; do
  code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "$URLBASE$path" || echo 000)
  printf '%s %s\n' "$code" "$URLBASE$path"
  [ "$code" = 200 ] || { echo "deploy check failed: $path" >&2; exit 1; }
done
