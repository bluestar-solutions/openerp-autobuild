#!/bin/sh

tar czf oebuild.tar.gz src/ install.sh --transform s,src,oebuild/oebuild, --transform s,install.sh,oebuild/install.sh, --exclude=*.pyc
