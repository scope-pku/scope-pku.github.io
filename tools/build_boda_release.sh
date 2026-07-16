#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=${1:-"$root/dist/boda-site"}
case "$out" in
  /*) ;;
  *) out="$root/$out" ;;
esac
path_prefix=${BODA_PATH_PREFIX:-}

if [ "$path_prefix" = "/" ]; then
  path_prefix=
elif [ -n "$path_prefix" ]; then
  if ! printf '%s\n' "$path_prefix" | rg -q '^(/[A-Za-z0-9_-]+)+/?$'; then
    echo "BODA_PATH_PREFIX must be empty or use /safe/path segments." >&2
    exit 1
  fi
  path_prefix=${path_prefix%/}
fi

hash_file() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1"
  else
    shasum -a 256 "$1"
  fi
}

rm -rf "$out"
mkdir -p "$out"
hugo --source "$root/site" --destination "$out" \
  --cleanDestinationDir --environment production \
  --baseURL "https://xulm.pku.edu.cn${path_prefix}/"

# Hugo always emits an /en/ redirect for the default language in multilingual
# mode. English already lives at the root, and this release has no aliases.
rm -rf "$out/en"

# Boda prepends a UTF-8 BOM to uploaded CSS and JavaScript, which invalidates
# Hugo's subresource-integrity hashes and makes browsers reject those assets.
find "$out" -type f \( -name '*.html' -o -name '*.htm' \) \
  -exec sed -i.bak 's/ integrity="sha256-[^"]*"//g' {} +
find "$out" -type f -name '*.bak' -delete

if [ -n "$path_prefix" ]; then
  find "$out" -type f \( -name '*.html' -o -name '*.htm' \) \
    -exec sed -i.bak \
      -e "s#=\"${path_prefix}/#=\"__BODA_PREFIX__/#g" \
      -e "s#=\"/\\([^/]\\)#=\"${path_prefix}/\\1#g" \
      -e "s#=\"/\"#=\"${path_prefix}/\"#g" \
      -e "s#=\"__BODA_PREFIX__/#=\"${path_prefix}/#g" {} +
  find "$out" -type f -name '*.bak' -delete
fi

# xulm.pku.edu.cn currently serves index.htm for the bare domain.
cp "$out/index.html" "$out/index.htm"

if rg -l 'localhost|127\.0\.0\.1|livereload|\.vsb' "$out" >/dev/null; then
  echo "Release contains development or legacy VSB references." >&2
  exit 1
fi

if find "$out" -type f | sed 's#.*/##' | rg '[^A-Za-z0-9._-]' >/dev/null; then
  echo "Release contains a filename rejected by Boda." >&2
  exit 1
fi

if rg -l ' integrity=' "$out" -g '*.html' -g '*.htm' >/dev/null; then
  echo "Release contains subresource-integrity attributes rejected by Boda." >&2
  exit 1
fi

commit=$(git -C "$root" rev-parse --verify HEAD)
if [ -n "$(git -C "$root" status --porcelain=v1 --untracked-files=all)" ]; then
  dirty=true
else
  dirty=false
fi
printf '{"commit":"%s","dirty":%s,"schema":1}\n' "$commit" "$dirty" \
  > "$out/BODACLI_BUILD.json"

(
  cd "$out"
  find . -type f ! -name SHA256SUMS ! -name BODACLI_BUILD.json | LC_ALL=C sort |
    while IFS= read -r file; do hash_file "$file"; done
) > "$out/SHA256SUMS"

cmp "$out/index.html" "$out/index.htm"
echo "Built $(find "$out" -type f | wc -l | tr -d ' ') files at $out ($(du -sh "$out" | cut -f1))."
