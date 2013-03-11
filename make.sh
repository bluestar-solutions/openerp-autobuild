#/bin/sh

TARGET_DIR=target
VERSION=$(git describe --exact-match --abbrev=0)

rm -Rf $TARGET_DIR
mkdir -p $TARGET_DIR/openerp-autobuild
cp -R debian $TARGET_DIR/openerp-autobuild/
cp openerp-autobuild.py $TARGET_DIR/openerp-autobuild/openerp-autobuild

cd $TARGET_DIR/openerp-autobuild
dch --create -v $VERSION --package openerp-autobuild
debuild -i -us -uc -b

