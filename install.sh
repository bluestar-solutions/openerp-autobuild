#!/bin/sh

if [ "$(/usr/bin/id -u)" != "0" ]; then
	echo "This script must be run as root" 1>&2
	exit 1
fi

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

DEFAULT_DESTPATH="/usr/lib/oebuild"

read -p "Install path [$DEFAULT_DESTPATH]:" DESTPATH
DESTPATH="${DESTPATH:-$DEFAULT_DESTPATH}"

cp "$SCRIPTPATH/oebuild" "$DESTPATH"
cp "$DESTPATH/conf/default_etc_config.json" "/etc/oebuild_config.json"
