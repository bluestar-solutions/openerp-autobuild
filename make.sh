#/bin/sh

TARGET_DIR=target
VERSION=1.5-1

rm -Rf $TARGET_DIR
mkdir -p $TARGET_DIR/openerp-autobuild
cp -R debian $TARGET_DIR/openerp-autobuild/
cp src/* $TARGET_DIR/openerp-autobuild/

cd $TARGET_DIR/openerp-autobuild
dch --create -v $VERSION --package openerp-autobuild-1-5
debuild -i -us -uc -b

