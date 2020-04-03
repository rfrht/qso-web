#!/bin/bash

echo "Content-type: text/html"
echo ""

source /etc/qso/qso.conf

# URL Decoder
urldecode() { echo -e "$(sed 's/+/ /g;s/%\(..\)/\\x\1/g;')"; }

read -N $CONTENT_LENGTH QUERY_STRING_POST
QS=($(echo $QUERY_STRING_POST | tr '&' ' '))
CALLSIGN=$(echo ${QS[0]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -15 | tr "[:lower:]" "[:upper:]" )

CONTATOS=$(sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), obs, mode FROM contacts WHERE callsign = '$CALLSIGN' OR op LIKE '%$CALLSIGN%' ORDER BY qtr DESC;" |
           awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td></tr>"}')
QTD_CONTATOS=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN'")
CONTATOS_ESTE_ANO=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN' AND strftime('%Y',qtr,'unixepoch') = strftime('%Y','now');")

echo "
<html>
<header>
<title>Listagem de contatos - $CALLSIGN</title></header>
<body bgcolor='#ffbd00'>
<h1>Rela&ccedil;&atilde;o de QSOs com <a href=https://www.qrz.com/db/$CALLSIGN>$CALLSIGN</a></h1>"

TZ='America/Sao_Paulo' date ; echo "<P>"

echo "<h2>Contatos: $QTD_CONTATOS</h2>
<h3>Este ano: $CONTATOS_ESTE_ANO</h3>"

echo "<table border=1><TR><TD><B>QRG</B></TD><TD><B>Indicativo</B></TD><TD><B>Operador</B></TD><TD><B>QTR</B></td><TD><B>Notas</B></td><TD><B>Modo</B></td></tr>"

echo "$CONTATOS"

echo "</table>
</body>
</html>"

exit 0
