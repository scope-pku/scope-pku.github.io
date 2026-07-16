#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
exec ./tools/bodacli crud-test \
  --path-prefix /test \
  --apply \
  --confirm BODA_CRUD_TEST
