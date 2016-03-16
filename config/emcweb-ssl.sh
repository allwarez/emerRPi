#!/bin/bash

grep -v ^exit /etc/rc.local > /etc/rc.local.new
echo -e "[ ! -f /etc/ssl/private/emcweb.key ] || [ ! -f /etc/ssl/certs/emcweb.crt ] && openssl req -nodes -x509 -newkey rsa:4096 -keyout /etc/ssl/private/emcweb.key -out /etc/ssl/certs/emcweb.crt -days 3560 -subj /C=US/ST=Oregon/L=Portland/O=IT/CN=emercoin.local\n\nexit 0\n" >> /etc/rc.local.new
mv -f /etc/rc.local.new /etc/rc.local
chmod +x /etc/rc.local
