#!/bin/bash

NBFILE="/home/hduser/nbserver.pem"
if [ ! -f $NBFILE ];
then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -subj "/C=US/ST=Izhar/L=Stockholm/O=Dis/CN=www.example.com" \
    -keyout /home/hduser/nbserver.pem \
    -out /home/hduser/nbserver.pem
    mkdir /home/hduser/notebooks
fi

PASSWD_FILE=/home/hduser/.ipython/profile_nbserver/nbpasswd.txt

if [ ! -f $PASSWD_FILE ];
 then
     python -c "from IPython.lib import passwd; print passwd()" > $PASSWD_FILE
fi

cd /home/hduser/notebooks
ipython notebook --profile=nbserver

