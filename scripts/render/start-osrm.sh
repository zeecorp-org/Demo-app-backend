#!/bin/sh
set -eu

DATA_DIR="${OSRM_DATA_DIR:-/data}"
EXTRACT_FILE="${OSRM_EXTRACT_FILE:-region.osm.pbf}"
GRAPH_BASENAME="${OSRM_GRAPH_BASENAME:-region}"
LUA_PROFILE="${OSRM_LUA_PROFILE:-car}"
EXTRACT_URL="${OSRM_EXTRACT_URL:-}"

EXTRACT_PATH="${DATA_DIR}/${EXTRACT_FILE}"
GRAPH_PATH="${DATA_DIR}/${GRAPH_BASENAME}.osrm"

download_extract() {
  if command -v curl >/dev/null 2>&1; then
    curl -L --fail --retry 3 "$1" -o "$2"
    return
  fi

  if command -v wget >/dev/null 2>&1; then
    wget -O "$2" "$1"
    return
  fi

  echo "Neither curl nor wget is available to download ${EXTRACT_FILE}."
  exit 1
}

mkdir -p "$DATA_DIR"

if [ ! -f "$EXTRACT_PATH" ]; then
  if [ -z "$EXTRACT_URL" ]; then
    echo "Missing ${EXTRACT_PATH}. Set OSRM_EXTRACT_URL to auto-download an extract."
    exit 1
  fi

  echo "Downloading OSM extract from ${EXTRACT_URL}"
  download_extract "$EXTRACT_URL" "$EXTRACT_PATH"
fi

if [ ! -f "$GRAPH_PATH" ]; then
  echo "Preparing OSRM graph files for ${EXTRACT_FILE}"
  osrm-extract -p "/opt/${LUA_PROFILE}.lua" "$EXTRACT_PATH"
  osrm-partition "$GRAPH_PATH"
  osrm-customize "$GRAPH_PATH"
fi

exec osrm-routed --algorithm mld --port "${PORT:-5000}" "$GRAPH_PATH"
