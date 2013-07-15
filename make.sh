#/bin/sh

TARGET_DIR=target
VERSION=$(git describe --abbrev=0 --tags)

rm -Rf $TARGET_DIR
mkdir -p $TARGET_DIR/openerp-autobuild
cp -R debian $TARGET_DIR/openerp-autobuild/
cp openerp-autobuild.py $TARGET_DIR/openerp-autobuild/openerp-autobuild.py
cp openerp-autobuild-1.5.py $TARGET_DIR/openerp-autobuild/openerp-autobuild-1.5.py
cp oebuild_logger.py $TARGET_DIR/openerp-autobuild/oebuild_logger.py
cp oebuild_conf_schema.py $TARGET_DIR/openerp-autobuild/oebuild_conf_schema.py
cp oebuild_conf_schema_1_5.py $TARGET_DIR/openerp-autobuild/oebuild_conf_schema_1_5.py

cd $TARGET_DIR/openerp-autobuild
dch --create -v $VERSION --package openerp-autobuild
debuild -i -us -uc -b

