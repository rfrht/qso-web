#!/bin/bash

echo "Content-type: text/html"
echo ""

# Source config stuff
source /etc/qso/qso.conf

#DEBUG=1

if [ $DEBUG == 1 ] ; then
   exec 2>&1
   set -e -x
fi

# URL Decoder
urldecode() { echo -e "$(sed 's/+/ /g;s/%\(..\)/\\x\1/g;')"; }

# Read the form POST and sanitize it
read -N $CONTENT_LENGTH QUERY_STRING_POST
QS=($(echo $QUERY_STRING_POST | tr '&' ' '))
CALLSIGN=$(echo ${QS[0]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -15 | tr "[:lower:]" "[:upper:]" )
METHOD=$(echo ${QS[1]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" )
DATE=$(echo ${QS[2]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -11 )
VIA=$(echo ${QS[3]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -15 | tr "[:lower:]" "[:upper:]" )
TYPE=$(echo ${QS[4]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" )

# Check for essential fields
if [ -z "$CALLSIGN" ] ; then
  echo "<h1>Faltou campo essencial</h1>"
  exit 1
# If only call and no more info - list the contacts
elif [[ -z "$TYPE" || -z "$METHOD" ]] ; then
# If there's already a QSL card for this contact, list it and stop.
  QSLS=$(sqlite $SQDB "SELECT COUNT(*) FROM qsl WHERE callsign = '$CALLSIGN'")
  if [[ $QSLS -ge 1 ]] ; then
    cat $QSL_FORM | sed -e "s/\"F1f/$CALLSIGN\"/g"
    sqlite -separator ',' $SQDB "SELECT rowid, callsign, method, datetime(date,'unixepoch'), via, type FROM qsl
                             WHERE callsign='$CALLSIGN' ORDER BY date" |
    awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td></tr>"}'
    echo "</table>"
    exit 0
  fi
# No previous QSL cards - list previous contacts, oldest first.
  cat $QSL_FORM | sed -e "s/\"F1f/$CALLSIGN\"/g" -e "/Method/d"
  echo "<table border=1><TR><TD><B>RADIO</B></TD><TD><B>MODE</B></TD><TD><B>HIS SIG</B></TD><TD><B>FREQUENCY</B></td><TD><B>QTR</B></td><TD><B>NOTES</B></td><td><B>TX POWER</B></td><td><B>SERIAL</B></td><td><B>OP</B></td></tr>"
  CONTATOS=$(sqlite -separator ',' $SQDB "SELECT callsign, mode, sighis, qrg, strftime('ON: %d/%m/%Y - AT %H:%M', qtr,'unixepoch'), obs, power, rowid, op FROM contacts WHERE callsign = '$CALLSIGN' ORDER BY qtr ASC;" | 
  awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td><TD>"$9"</td></tr>"}')
  echo "$CONTATOS"
  exit 0
fi

# TNX or SWL - I already have the card, so XO = 1
if [[ "$TYPE" == "TNX" || "$TYPE" == "SWL" ]] ; then
   XO=1
else
# No card yet.
   XO=0
fi

# Prepare the QSO date.
if [[ -n $DATE ]] ; then
   EPOCH=$(TZ=UTC date +%s --date="$DATE")
else
   EPOCH=$(TZ=UTC date +%s)
fi
if [ -z $EPOCH ] ; then echo "Erro de Data" ; exit 1 ; fi

cat $QSL_FORM

# Logs the contact in SQLite DB
if [[ -n $SQDB ]] ; then
  if ! /usr/bin/sqlite $SQDB "INSERT INTO qsl (callsign, method, date, via, type, xo) VALUES ('$CALLSIGN', '$METHOD', '$EPOCH', '$VIA', '$TYPE', '$XO')" >/dev/shm/transaction-sqlite.log 2>&1; then
    echo "<P>Problemas ao registrar o SQLite</p>"
  else
    echo "SQLite OK<BR>"
  fi
fi

# Show the last 20 QSL confirmations after logging the Contact
sqlite -separator ',' $SQDB "SELECT rowid, callsign, method, datetime(date,'unixepoch'), via, type FROM qsl
                             WHERE strftime('%Y',date,'unixepoch') = strftime('%Y','now') ORDER BY date DESC LIMIT 20" |
  awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td></tr>"}'

echo "</table></body></html>"
