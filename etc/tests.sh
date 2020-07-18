#!/usr/bin/env bash

cd  $Ell
pypy3 -m bnbad -T
echo "Status: $?"
exit $?
