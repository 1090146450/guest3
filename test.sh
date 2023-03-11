#! /bin/bash
echo "进入虚拟环境"
source /home/an/python_guest3/bin/activate python_guest
echo "进入成功"
cd /home/an/guest3
pip3 install -r requirments.txt
du="`netstat -ntulp|grep 8001`"
if [[ "${du}" != "" ]];then
 lis=$IFS
 IFS=" "
 ardu=($du)
 IFS=$lis
 for var in ${ardu[@]}
  do
  if [[ "${var}" =~ "/" ]]; then
   dd=$IFS
   IFS="/"
   tes=($var)
   IFS=$dd
   echo "进程号为:"${tes}
   kill -9 ${tes}
   echo "kill success"
  fi
 done
else
 echo "无进程直接创建"
fi
sellp 2
uwsgi --ini uwsgi.ini
echo "启动uwsgi成功"
nginx -s reload
echo "重启NGINX"
git add .
git commit -m "更新PID"
git push origin master

