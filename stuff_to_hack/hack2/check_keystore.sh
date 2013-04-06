#! /bin/bash

case $1 in
    put)
        curl -d key=$3 -d value=$3 $2:8002/store
        ;;
    get)
        OUT=$(curl -d key=$3 $2:8002/retrieve)
        if [[ $OUT != $3 ]]
        then
            exit 1
        else
            exit 0
        fi
        ;;
    *)
        exit 1
        ;;
esac

