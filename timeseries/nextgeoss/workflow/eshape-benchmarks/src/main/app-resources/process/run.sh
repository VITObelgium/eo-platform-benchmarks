#!/bin/bash

source ${_CIOP_APPLICATION_PATH}/process/lib/functions.sh

trap cleanExit EXIT

# Input references come from STDIN (standard input) and they are retrieved
# line-by-line.
while read input
do
  main ${input} || exit $?
done
