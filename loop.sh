#!/bin/bash
while true
do
    for dir in KR NA
    do
        cd $dir
        cat urls.txt | xargs wget -N
        cd ..
    done
    git add */*xml
    git commit -m "automatic commit"
    git push origin master
    sleep 5m
done
