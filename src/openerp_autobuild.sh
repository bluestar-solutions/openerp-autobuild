#!/bin/bash
# PYTHON_ARGCOMPLETE_OK

CURRENT_VERSION="2.2"

# Set a temp workdir if oebuild is run in dev mode (-A in args)
if [[ "${@#-A}" = "$@" ]]; then
    WORKDIR="$HOME/.config/openerp-autobuild"
else
    WORKDIR="/tmp/oebuild"
fi

VENV="$WORKDIR/venv"
VERSION="$WORKDIR/venv_version"
PIP="$VENV/bin/pip"
PYTHON="$VENV/bin/python"
SCRIPT_PATH=`realpath "$0"`
OEBUILD_PATH=`dirname $SCRIPT_PATH`
echo "Use virtualenv : $VENV"

function rebuild_venv {
    rm -Rf $VENV
    python -m virtualenv "$VENV"
    $PIP install -r $OEBUILD_PATH/requirements.txt
    echo "$CURRENT_VERSION" >> $VERSION
}

if [ ! -d "$VENV" ]; then
    # VENV is not a directory
    rebuild_venv
elif [ ! -f "$VERSION" ]; then
    # VERSION is not a file
    rebuild_venv
elif [ "$(cat $VERSION)" != "$CURRENT_VERSION" ]; then
    # VERSION is not the expected one, this is to force venv rebuild
    # when oebuild version change.
    rebuild_venv
fi

$PYTHON $OEBUILD_PATH/openerp_autobuild.py $@
