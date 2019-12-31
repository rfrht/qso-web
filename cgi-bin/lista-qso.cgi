#!/bin/bash

echo "Content-type: text/html"
echo ""

source /etc/qso/qso.conf

echo "
<html>
<header>
<title>Rela&ccedil;&atilde;o de QSOs 2019 - $MY_CALLSIGN</title></header>
<body bgcolor='#ffbd00'>
<h1>Rela&ccedil;&atilde;o de QSOs 2019 - <a href=https://www.qrz.com/db/$MY_CALLSIGN>$MY_CALLSIGN</a></h1>"

TZ='America/Sao_Paulo' date ; echo "<P>"

cat $PAGE_HEADER

tac $QSO_LOGFILE | awk -F , '{printf  "<TR><TD>" $1 "</td><TD>" $2 "</td><TD>" $3 "</td><td>" $4 "</td><td>" $5 "</td><td>" $6 "</td><TD>" $7 "</td><TD>" $8 "</td></tr>"}'

echo "</table>
</body>
</html>"

exit 0
