#!/bin/sh

if [ "$(/usr/bin/id -u)" != "0" ]; then
	echo "This script must be run as root" 1>&2
	exit 1
fi

command -v pip >/dev/null 2>&1 || { 
	echo "pip is required but not installed."
	echo "On a Debian-based system, use 'apt-get install python-pip' to install it."
	echo "Installation aborted." 
	exit 1 
}
command -v bzr >/dev/null 2>&1 || { 
	echo "bzr is required but not installed."
	echo "On a Debian-based system, use 'apt-get install bzr' to install it."
	echo "Installation aborted." 
	exit 1 
} 
command -v pg_config >/dev/null 2>&1 || { 
	echo "pg_config is required but not installed."
	echo "On a Debian-based system, use 'apt-get install libpq-dev' to install it."
	echo "Installation aborted." 
	exit 1 
} 
command -v virtualenv >/dev/null 2>&1 || { 
	echo "virtualenv is required but not installed."
	echo "On a Debian-based system, use 'apt-get install python-virtualenv' to install it."
	echo "Installation aborted." 
	exit 1 
} 
python_loc=`whereis -b python.h | cut -c9-`
if [ -e "$python_loc" ]; then
	echo "Python headers (python.h) are required but not installed."
	echo "On a Debian-based system, use 'apt-get install python-dev' to install it."
	echo "Installation aborted."
	exit 1
fi;
libldap2_loc=`whereis -b lber.h | cut -c7-`
if [ -e "$libldap2_loc" ]; then
	echo "OpenLDAP headers (lber.h) are required but not installed."
	echo "On a Debian-based system, use 'apt-get install libldap2-dev' to install it."
	echo "Installation aborted."
	exit 1
fi;
libsasl2_loc=`whereis -b sasl.h | cut -c7-`
if [ -e "$libsasl2_loc" ]; then
	echo "libsasl2 headers (sasl.h) are required but not installed."
	echo "On a Debian-based system, use 'apt-get install libsasl2-dev' to install it."
	echo "Installation aborted."
	exit 1
fi;
libxml2_loc=`whereis -b libxml2 | cut -c8-`
if [ -e "$libxml2_loc" ]; then
	echo "libxml2 headers (libxml2/libxml/xmlversion.h) are required but not installed."
	echo "On a Debian-based system, use 'apt-get install libxml2-dev libxslt-dev' to install it."
	echo "Installation aborted."
	exit 1
fi;

pip install --upgrade jsonschema psycopg2 GitPython argcomplete

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")cd 

DEFAULT_DESTPATH="/usr/lib/oebuild"

read -p "Install path [$DEFAULT_DESTPATH]:" DESTPATH
DESTPATH="${DESTPATH:-$DEFAULT_DESTPATH}"

if [ -d "$DESTPATH" ]
then
	while true; do
		read -p "$DESTPATH already exists, do you want to overwrite it? [y/N] " yn
		case ${yn:'n'} in
		[Yy]* ) 
			rm -Rf "$DESTPATH"
			break
			;;
		[Nn]* ) 
			echo "Installation aborted."
			exit
			;;
		* ) 
			echo "Please answer yes or no."
			;;
		esac
	done
fi

cp -R "$SCRIPTPATH/oebuild" "$DESTPATH"
cp "$DESTPATH/conf/default_etc_config.json" "/etc/oebuild_config.json"

rm -f "/usr/bin/openerp-autobuild"
rm -f "/usr/bin/oebuild"
ln -s "$DESTPATH/openerp_autobuild.py" "/usr/bin/openerp-autobuild"
ln -s "$DESTPATH/openerp_autobuild.py" "/usr/bin/oebuild"

activate-global-python-argcomplete

echo "openerp-autobuild successfully installed !"
