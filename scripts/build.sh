#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
case "$VERSION" in
  22.04|24.04|26.04) ;;
  *)
    echo "Usage: $0 {22.04|24.04|26.04}" >&2
    exit 2
    ;;
esac

TAG="mdt-linux-configurator:${VERSION}"
docker build -f "docker/Dockerfile.${VERSION}" -t "$TAG" .
echo "Built $TAG"
