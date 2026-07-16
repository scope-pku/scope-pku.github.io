#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
out=${1:-"$root/dist/boda-site"}

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
  --cleanDestinationDir --environment production

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

(
  cd "$out"
  find . -type f ! -name SHA256SUMS | LC_ALL=C sort |
    while IFS= read -r file; do hash_file "$file"; done
) > "$out/SHA256SUMS"

cmp "$out/index.html" "$out/index.htm"
echo "Built $(find "$out" -type f | wc -l | tr -d ' ') files at $out ($(du -sh "$out" | cut -f1))."
