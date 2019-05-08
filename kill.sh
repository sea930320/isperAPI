for i in `ps -ef|grep isper2019.wsgi|grep -v grep|awk '{print $2}'`
do
kill -9 $i
done
