for i in `ps -ef|grep isper-api.wsgi|grep -v grep|awk '{print $2}'`
do
kill -9 $i
done
