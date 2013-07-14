#!/bin/bash
while true
do
    for dir in KR NA
    do
        cd $dir
        cat urls.txt | xargs wget -N
        git add *xml
        cd ..
    done
    cd Hikki
    python grab.py
    git add *json *py
    cd ../
    git commit -m "automatic commit"
    git push origin master
    sleep 5m
done
