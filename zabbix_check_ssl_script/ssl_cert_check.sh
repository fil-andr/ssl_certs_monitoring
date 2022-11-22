#! /bin/sh

DEBUG=0
if [ $DEBUG -gt 0 ]
then
    exec 2>>/tmp/my.log
    set -x
fi

f=$1
host=$2
port=$3
sni=$4
proto=$5

if [ -z "$sni" ]
then
    servername=$host
else
    servername=$sni
fi

if [ -n "$proto" ]
then
    starttls="-starttls $proto"
fi

case $f in
-d)
end_date=`echo QUIT |  openssl s_client -servername $servername -connect $host:$port 2>/dev/null | openssl x509 -noout -dates | sed -n 's/ *notAfter= *//p'`

#echo $end_date


if [ -n "$end_date" ]
then
    end_date_seconds=`date '+%s' --date "$end_date"`
    now_seconds=`date '+%s'`
    echo "($end_date_seconds-$now_seconds)/24/3600" | bc
fi
;;

-i)
issue_dn=`echo QUIT |  openssl s_client -servername $servername -connect $host:$port 2>/dev/null | openssl x509 -noout -dates  | sed -n 's/ *Issuer: *//p'`

if [ -n "$issue_dn" ]
then
    issuer=`echo $issue_dn | sed -n 's/.*CN=*//p'`
    echo $issuer
fi
;;
*)
echo "usage: $0 [-i|-d] hostname port sni"
echo "    -i Show Issuer"
echo "    -d Show valid days remaining"
;;
esac
