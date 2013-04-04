#! /bin/bash

while [ 1 ]; do
nc -l -p 8001 -e "./lser"
done
