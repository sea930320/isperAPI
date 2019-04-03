for i in `ps -ef|grep lets2017.wsgi|grep -v grep|awk '{print $2}'`
do
kill -9 $i
done
