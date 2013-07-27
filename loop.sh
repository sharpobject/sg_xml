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
    sed 's/&/&amp;/' < ../NA/en_cardData.xml > en_cardData.xml
    sed 's/&/&amp;/' < ../NA/en_cardSkill.xml > en_cardSkill.xml
    python grab.py
    git add *json *py timestamp
    cd ../
    git add loop.sh
    git commit -m "automatic commit"
    git push origin master
    sleep 10m
done
