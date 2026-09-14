#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
  printf '%s\n' "Usage: scripts/release.sh vX.Y.Z" >&2
  exit 2
fi

case "$VERSION" in
  v[0-9]*.[0-9]*.[0-9]*) ;;
  *)
    printf '%s\n' "Version must look like v0.1.0" >&2
    exit 2
    ;;
esac

python3 -m unittest discover -s tests
git tag "$VERSION"
printf '%s\n' "Created tag $VERSION. Push it to trigger the release workflow."
