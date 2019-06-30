#!/bin/bash

echo "Content-type: text/html"
echo ""

# Source config stuff
source /etc/qso.conf

# Calculate serial number
LOG_RECORDS=$(wc -l $QSO_LOGFILE | awk '{print $1}')
let SERIAL=PRECOUNT+LOG_RECORDS+1

# Read the form POST and sanitize it
read -N $CONTENT_LENGTH QUERY_STRING_POST
QS=($(echo $QUERY_STRING_POST | tr '&' ' '))
QRG=$(echo ${QS[2]} | awk -F = '{print $2}' | tr -dc '[:print:]' | cut -b -8)
CALLSIGN=$(echo ${QS[0]} | awk -F = '{print $2}' | tr -dc '[:alnum:]' | cut -b -6 | tr "[:lower:]" "[:upper:]")
QRA=$(echo ${QS[1]} | awk -F = '{print $2}' | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" | /bin/sed 's/+/\ /g')
QTR=$(TZ=UTC date +%c)
OBS=$(echo ${QS[3]} | awk -F = '{print $2}' | tr -dc '[:print:]' | cut -b -40 | tr "[:lower:]" "[:upper:]" | /bin/sed 's/+/\ /g')
TX_POWER=$(echo ${QS[4]} | awk -F = '{print $2}' | tr -dc '[:digit:]' | cut -b -3 )
MODE=$(echo ${QS[5]} | awk -F = '{print $2}' | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]")
RST_R=$(echo ${QS[8]} | awk -F = '{print $2}' | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" | /bin/sed 's/+/\ /g')
RST_T=$(echo ${QS[7]} | awk -F = '{print $2}' | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" | /bin/sed 's/+/\ /g')
QSO_DATE=$(TZ=UTC date +%Y%m%d)
QSO_TIME=$(TZ=UTC date +%H%M)

# Stop logging if missing essential fields
if [[ -z $QRG || -z $CALLSIGN || -z $MODE ]] ; then
   echo "<h1>FALTOU CAMPO ESSENCIAL</h1>"
   # Reuse this QSO data in new contact form
   cat $RECORD_FORM | sed -e "s/\"Ff/$QRG\"/g" -e "s/\"$MODE\"/\"$MODE\" checked/g" -e "s/\"15\"/\"$TX_POWER\"/g"
   # List last 20 contacts
   tac $QSO_LOGFILE | head -n 20 | awk -F , '{printf  "<TR><TD>" $1 "</td><TD>" $2 "</td><TD>" $3 "</td><td>" $4 "</td><td>" $5 "</td><TD>" $6 "</td><TD>" $7 "</td></tr>"}'
   exit 0
fi

if [ -z $RST_R ] ; then
   OBS=$(echo QRA $QRA - $OBS )
else
   if [ $MODE == "FT8" ] ; then
      OBS=$(echo "QRA $QRA-$OBS-RST R $RST_R dB-RST T $RST_T dB")
   else
      OBS=$(echo "QRA $QRA-$OBS-RST R $RST_R-RST T $RST_T")
   fi
fi

# Logs the entry locally
if ! echo $QRG,$CALLSIGN,$QRA,$QTR,$OBS,$MODE,$SERIAL >> $QSO_LOGFILE ; then
   echo "<H1>Error Writing Local Log File $QSO_LOGFILE</h1>"
   exit 1
fi

# Reuse fields from this QSO to the next one
cat $RECORD_FORM | sed -e "s/\"Ff/$QRG\"/g" -e "s/\"$MODE\"/\"$MODE\" checked/g" -e "s/\"15\"/\"$TX_POWER\"/g"

# List last 20 contacts
tac $QSO_LOGFILE | head -n 20 | awk -F , '{printf  "<TR><TD>" $1 "</td><TD>" $2 "</td><TD>" $3 "</td><td>" $4 "</td><td>" $5 "</td><TD>" $6 "</td><TD>" $7 "</td></tr>"}'

ADIF_QRZ=$(echo "KEY=$QRZ_KEY&ACTION=INSERT&ADIF=<freq:${#QRG}>$QRG<mode:${#MODE}>$MODE<qso_date:${#QSO_DATE}>$QSO_DATE<call:${#CALLSIGN}>$CALLSIGN<time_on:${#QSO_TIME}>$QSO_TIME<comment:${#OBS}>$OBS<station_callsign:${#MY_CALLSIGN}>$MY_CALLSIGN<stx:${#SERIAL}>$SERIAL<tx_pwr:${#TX_POWER}>$TX_POWER<rst_rcvd:${#RST_R}>$RST_R<rst_sent:${#RST_T}>$RST_T<eor>")

EQSLMSG="TNX for QSO - ANT $ANTENNA1 - TX $TX_POWER W - QSO NR $SERIAL - QRZ/LOTW OK - 73s o/"
ADIF_EQSL=$(echo "ADIFData=Test upload<ADIF_VER:4>1.00<EQSL_USER:${#EQSL_USER}>$EQSL_USER<EQSL_PSWD:${#EQSL_PASS}>$EQSL_PASS<EOH><freq:${#QRG}>$QRG<mode:${#MODE}>$MODE<qso_date:${#QSO_DATE}>$QSO_DATE<call:${#CALLSIGN}>$CALLSIGN<time_on:${#QSO_TIME}>$QSO_TIME<qslmsg:${#EQSLMSG}>$EQSLMSG<station_callsign:${#MY_CALLSIGN}>$MY_CALLSIGN<stx:${#SERIAL}>$SERIAL<tx_pwr:${#TX_POWER}>$TX_POWER<rst_rcvd:${#RST_R}>$RST_R<rst_sent:${#RST_T}>$RST_T<eor>")

# Only logs QSO if not a blacklisted QRG
if ! [[ $SKIP_LOG == *$QRG* ]] ; then
   if ! curl -d "$ADIF_QRZ" -X POST https://logbook.qrz.com/api | grep "RESULT=OK" >/dev/null ; then 
      echo "<P>Problemas ao incluir no QRZ</P>"
      echo $ADIF_QRZ >> $QRZ_ERRLOG
   fi

   if ! curl -d "$ADIF_EQSL" -X POST https://www.eQSL.cc/qslcard/ImportADIF.cfm | grep "Result: 1" >/dev/null ; then 
      echo "<P>Problemas ao incluir no EQSL</P>"
      echo $ADIF_EQSL >> $EQSL_ERRLOG
   fi
fi

echo "</table>
</body>
</html>"
