#!/bin/bash

echo "Content-type: text/html; charset=UTF-8"
echo ""

source /etc/qso/qso.conf

echo "
<html>
<header>
<title>Rela&ccedil;&atilde;o de QSLs pagos - $MY_CALLSIGN</title></header>
<body bgcolor='#ffbd00'>
<h1>Rela&ccedil;&atilde;o de QSLs pagos - <a href=https://www.qrz.com/db/$MY_CALLSIGN>$MY_CALLSIGN</a></h1>"

TZ='America/Sao_Paulo' date ; echo "<P>"

cat $PAGE_HEADER | sed -e "/Watts/d"
echo "<table border><tr><td><b>S/N</td><td><b>Callsign</td><TD><B>Method</td><td><b>Date</td><td><b>Via</td><td><b>Type</td><td><b>X/O</td></tr>"

sqlite -separator ',' $SQDB "SELECT rowid, callsign, method, datetime(date,'unixepoch'), via, type, CASE xo WHEN 0 THEN '❌' WHEN 1 THEN '✅' END FROM qsl
                             ORDER BY date DESC" |
  awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD><center>"$7"</center></td></tr>"}'
echo "</table></body></html>"
