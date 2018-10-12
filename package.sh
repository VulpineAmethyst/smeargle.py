#!/bin/sh

DIR="smeargle-$1"

rm -rf smeargle/__pycache__
mkdir ${DIR}
cp -r smeargle ${DIR}
cp -a smeargle.py porygon.py girafarig.py readme.txt melissa8.{png,json} test.txt example.json ${DIR}
COPYFILE_DISABLE=1 tar cf ${DIR}.tar.bz2 ${DIR}
rm -r ${DIR}

