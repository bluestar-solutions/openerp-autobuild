#/bin/sh

TARGET_DIR=target

rm -Rf $TARGET_DIR
mkdir -p $TARGET_DIR
cp -R debian $TARGET_DIR/
cp openerp-autobuild.py $TARGET_DIR/openerp-autobuild

cd $TARGET_DIR/
dch -i
debuild --no-tgz-check

