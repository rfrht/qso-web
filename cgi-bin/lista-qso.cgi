#!/bin/bash

echo "Content-type: text/html"
echo ""

source /etc/qso/qso.conf

echo "
<html>
<header>
<title>Rela&ccedil;&atilde;o de QSOs 2020 - $MY_CALLSIGN</title></header>
<body bgcolor='#ffbd00'>
<h1>Rela&ccedil;&atilde;o de QSOs 2020 - <a href=https://www.qrz.com/db/$MY_CALLSIGN>$MY_CALLSIGN</a></h1>"

TZ='America/Sao_Paulo' date ; echo "<P>"

cat $PAGE_HEADER

sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), obs, mode, rowid, power FROM contacts 
                             WHERE strftime('%Y',qtr,'unixepoch') = strftime('%Y','now') ORDER BY qtr DESC" |
       awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td></tr>"}'

echo "</table>
</body>
</html>"
