#!/bin/bash

echo "Content-type: text/html"
echo ""

# Source config and functions
source /etc/qso/qso.conf
source /etc/qso/functions.sh

if [ $DEBUG == 1 ] ; then
   exec 2>&1
   set -e -x
   set
   env
fi

if [ -z "$QUERY_STRING" ] ; then
  read -N $CONTENT_LENGTH QUERY_STRING_POST
  QS=($(echo $QUERY_STRING_POST | tr '&' ' '))
  CALLSIGN=$(echo ${QS[0]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -15 )
else
  # Clicked to confirm a QSL card
  QSL_SERIAL=$(echo $QUERY_STRING | awk -F = '{print $2}')
  CALLSIGN=$(sqlite $SQDB "SELECT callsign FROM qsl WHERE rowid = $QSL_SERIAL")
  sqlite $SQDB "UPDATE qsl SET xo = 1 WHERE rowid = $QSL_SERIAL"
fi

CONTATOS=$(sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), qth, mode, serial, power, obs, sighis, sigmy FROM contacts 
                                        WHERE callsign = '$CALLSIGN' OR op LIKE '%$CALLSIGN%' ORDER BY qtr DESC;" |
           awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td><TD>"$9"</td><TD>"$10"</td><TD>"$11"</td></tr>"}')
QTD_CONTATOS=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN'")
CONTATOS_ESTE_ANO=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN' 
                                  AND strftime('%Y',qtr,'unixepoch') = strftime('%Y','now');")

echo "
<html>
<header>
<title>Listagem de contatos - $CALLSIGN - $QSL_SERIAL</title></header>
<body bgcolor='#ffbd00'>
<h1>Rela&ccedil;&atilde;o de QSOs com <a href=https://www.qrz.com/db/$CALLSIGN>$CALLSIGN</a></h1>"

TZ='America/Sao_Paulo' date ; echo "<P>"

if [[ $QTD_CONTATOS -ge 1 ]] ; then
  QSLS=$(sqlite $SQDB "SELECT COUNT(*) FROM qsl WHERE callsign = '$CALLSIGN'")
  if [[ $QSLS -ge 1 ]] ; then
    echo "<P>QSLs pagos:</P>"
    echo "<table border><tr><td><b>Callsign</td><TD><B>Method</td><td><b>Date</td><td><b>Via</td><td><b>Type</td><td><b>X/O</td></tr>"
    sqlite -separator ',' $SQDB "SELECT callsign, method, datetime(date,'unixepoch'), via, type, 
                                 CASE xo WHEN 0 THEN 'O' WHEN 1 THEN 'X' END, rowid FROM qsl
                                 WHERE callsign='$CALLSIGN' ORDER BY date" |
    awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD><center><a href=conta-contatos.cgi?qsl="$7">"$6"</a></center></td></tr>"}'
    echo "</table>"
  else
    HAS_BUREAU=$(check_bureau $CALLSIGN)
    echo "<form action="/cgi-bin/registra-qsl.cgi" method="POST"><table border><tr>"
    if [ -z "$HAS_BUREAU" ] ; then 
      echo "<TD><B>No Bureau</b></td>"
    else
      echo "<td>$HAS_BUREAU</td>"
    fi
    echo "<td align=center>
    <input type="hidden" name="callsign" value="$CALLSIGN">
    <input type="SUBMIT" value="Pagar"></form></td></tr></table>"
  fi
fi

echo "<h2>Contatos: $QTD_CONTATOS</h2>
<h3>Este ano: $CONTATOS_ESTE_ANO</h3>"

echo "<table border><tr><td><b>QRG (MHz)</td><TD><B>Indicativo</td><td><b>Operador</td><td><b>QTR (GMT)</td><td><b>QTH</td><td><b>Modo</td><td><b>Serial</td><TD><B>Watts</b></td><TD><B>ObS</b></td><TD><B>His Sig</b></td><TD><B>My Sig</b></td></tr>"

echo "$CONTATOS"

echo "</table>
</body>
</html>"

exit 0
