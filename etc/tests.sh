#!/usr/bin/env bash

cd  $Ell
python3 -m bnbad -T
echo "Status: $?"
exit $?
