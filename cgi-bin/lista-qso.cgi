#!/bin/bash

echo "Content-type: text/html"
echo ""

source /etc/qso/qso.conf

if [ $DEBUG == 1 ] ; then
   exec 2>&1
   set -e -x
fi

export TZ=America/Sao_Paulo

YEAR=$(echo $REQUEST_URI | awk -F - '{print $4}' | sed -e 's/\.cgi//g')

if [ -z "$YEAR" ] ; then YEAR=$(date +%Y) ; fi

JAN=$(date +%s --date="Jan 1 $YEAR")
DEC=$(date +%s --date="Jan 1 $(($YEAR + 1))")

echo "
<html>
<header>
<title>Rela&ccedil;&atilde;o de QSOs $YEAR - $MY_CALLSIGN</title></header>
<body bgcolor='#ffbd00'>
<h1>Rela&ccedil;&atilde;o de QSOs $YEAR - <a href=https://www.qrz.com/db/$MY_CALLSIGN>$MY_CALLSIGN</a></h1>"

date ; echo "<P>"

cat $PAGE_HEADER

sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, date(qtr,'unixepoch'), qth, mode, serial, power, obs, sighis, sigmy FROM contacts 
                             WHERE qtr >= $JAN AND qtr < $DEC ORDER BY qtr DESC" |
       awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td><TD>"$9"</td><TD>"$10"</td><TD>"$11"</td></tr>"}'

echo "</table>
</body>
</html>"
