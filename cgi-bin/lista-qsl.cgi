#!/bin/bash

echo "Content-type: text/html"
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
echo "<table border><tr><td><b>Callsign</td><TD><B>Method</td><td><b>Date</td><td><b>Via</td><td><b>Type</td></tr>"

sqlite -separator ',' $SQDB "SELECT callsign, method, datetime(date,'unixepoch'), via, type FROM qsl
                             WHERE strftime('%Y',date,'unixepoch') = strftime('%Y','now') ORDER BY date DESC" |
  awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td></tr>"}'
echo "</table></body></html>"


