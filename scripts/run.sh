#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
DEVICE="${2:-/dev/ttyUSB0}"

case "$VERSION" in
  22.04|24.04|26.04) ;;
  *)
    echo "Usage: $0 {22.04|24.04|26.04} [/dev/ttyUSB0]" >&2
    exit 2
    ;;
esac

if [[ ! -e "$DEVICE" ]]; then
  echo "Serial device not found: $DEVICE" >&2
  exit 1
fi

if [[ -z "${DISPLAY:-}" ]]; then
  echo "DISPLAY is not set. Run from a graphical X11/XWayland session." >&2
  exit 1
fi

TAG="mdt-linux-configurator:${VERSION}"

docker run --rm -it \
  --device="$DEVICE:$DEVICE" \
  -e DISPLAY="$DISPLAY" \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  "$TAG"
