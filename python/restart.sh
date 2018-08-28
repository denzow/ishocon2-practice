#!/usr/bin/env bash
set -x
export BASE_DIR=/home/ishocon/webapp/python
echo 'mysql'
sudo cp ${BASE_DIR}/etc/mysql/my.cnf  /etc/mysql/my.cnf
sudo service mysql stop

echo 'nginx'
sudo cp ${BASE_DIR}/etc/nginx/nginx.conf  /etc/nginx/nginx.conf
sudo service nginx restart


#echo 'redis'
#sudo cp ${BASE_DIR}/etc/redis/redis.conf  /etc/redis/redis.conf
#sudo service redis restart
