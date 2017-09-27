#!/bin/bash

VENV=".oebuild/venv"
PIP="$VENV/bin/pip"
PYTHON="$VENV/bin/python"

if [ ! -d "$VENV" ]; then
    python -m virtualenv "$VENV"
    $PIP install -r `dirname "$0"`/requirements.txt
    echo "2.2" >> .oebuild/version
fi

$PYTHON `dirname "$0"`/openerp_autobuild.py $@
