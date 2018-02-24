#!/bin/sh

DIR="smeargle-$1"

mkdir ${DIR}
cp smeargle.py porygon.py readme.txt melissa8.{png,json} test.txt ${DIR}
COPYFILE_DISABLE=1 tar cf ${DIR}.tar.bz2 ${DIR}
rm -r ${DIR}

