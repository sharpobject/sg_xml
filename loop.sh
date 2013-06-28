#!/bin/bash
while true
do
    cd NA
    cat urls.txt | xargs wget
    cd ..
    git add */*xml
    git commit -m "automatic commit"
    git push origin master
    sleep 5m
done
