#!/bin/bash

PWD="$(pwd)"
PYTHON_VERSION="$1"
POETRY_ENV="$(poetry env info -p)"
SITE_PACKAGES="$(find ${POETRY_ENV}/lib -maxdepth 1 -mindepth 1 -type d -name python* -print0 -quit)/site-packages"
SRC_DIR="${POETRY_ENV}/src"

OUTPUT=""

if [ -d "${SRC_DIR}" ]; then
	OUTPUT="$(find ${SRC_DIR} -maxdepth 1 -mindepth 1 -type d -print)"
	OUTPUT="${OUTPUT//botus-receptus/botus-receptus/src}"
fi

OUTPUT="${OUTPUT}\n${PWD}"

echo -e "$OUTPUT" >| "$SITE_PACKAGES/easy-install.pth"