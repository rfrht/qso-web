#!/bin/bash

echo "Content-type: text/html"
echo ""

# URL Decoder
urldecode() { echo -e "$(sed 's/+/ /g;s/%\(..\)/\\x\1/g;')"; }

# Source config stuff
source /etc/qso.conf

# Calculate serial number
LOG_RECORDS=$(wc -l $QSO_LOGFILE | awk '{print $1}')
let SERIAL=PRECOUNT+LOG_RECORDS+1

# Read the form POST and sanitize it
read -N $CONTENT_LENGTH QUERY_STRING_POST
QS=($(echo $QUERY_STRING_POST | tr '&' ' '))
QRG=$(echo ${QS[2]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -8 )
CALLSIGN=$(echo ${QS[0]} | awk -F = '{print $2}' | urldecode | tr -dc '[:alnum:]' | cut -b -9 | tr "[:lower:]" "[:upper:]" )
QRA=$(echo ${QS[1]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" )
QTR=$(TZ=UTC date +%c)
OBS=$(echo ${QS[3]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -40 | tr "[:lower:]" "[:upper:]" )
TX_POWER=$(echo ${QS[4]} | awk -F = '{print $2}' | tr -dc '[:digit:]' | cut -b -3 )
MODE=$(echo ${QS[5]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" )
RST_R=$(echo ${QS[8]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" )
RST_T=$(echo ${QS[7]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 | tr "[:lower:]" "[:upper:]" )
QSO_DATE=$(TZ=UTC date +%Y%m%d)
QSO_TIME=$(TZ=UTC date +%H%M)

# Sort out the band
BAND=$(echo $QRG | awk -F . '{print $1}')
if   [[ $BAND == "1" ]] ; then BAND=160m
elif [[ $BAND == "3" ]] ; then BAND=80m
elif [[ $BAND == "5" ]] ; then BAND=60m
elif [[ $BAND == "7" ]] ; then BAND=40m
elif [[ $BAND == "10" ]] ; then BAND=30m
elif [[ $BAND == "14" ]] ; then BAND=20m
elif [[ $BAND == "18" ]] ; then BAND=17m
elif [[ $BAND == "21" ]] ; then BAND=15m
elif [[ $BAND == "24" ]] ; then BAND=12m
elif [[ $BAND -ge "28" && $BAND -lt "30" ]] ; then BAND=10m
elif [[ $BAND -ge "50" && $BAND -lt "54" ]] ; then BAND=6m
elif [[ $BAND -ge "144" && $BAND -lt "148" ]] ; then BAND=2m
elif [[ $BAND -ge "222" && $BAND -lt "225" ]] ; then BAND=1.25m
elif [[ $BAND -ge "420" && $BAND -lt "450" ]] ; then BAND=70cm
elif [[ $BAND -ge "902" && $BAND -lt "928" ]] ; then BAND=33cm
elif [[ $BAND -ge "1240" && $BAND -lt "1300" ]] ; then BAND=23cm
elif [[ $BAND -ge "2300" && $BAND -lt "2450" ]] ; then BAND=13cm
elif [[ $BAND -ge "3300" && $BAND -lt "3500" ]] ; then BAND=9cm
elif [[ $BAND -ge "5650" && $BAND -lt "5925" ]] ; then BAND=6cm
elif [[ $BAND -ge "10000" && $BAND -lt "10500" ]] ; then BAND=3cm
elif [[ $BAND -ge "24000" && $BAND -lt "24250" ]] ; then BAND=1.25cm
elif [[ $BAND -ge "47000" && $BAND -lt "47200" ]] ; then BAND=6mm
elif [[ $BAND -ge "75500" && $BAND -lt "81000" ]] ; then BAND=4mm
elif [[ $BAND -ge "119980" && $BAND -lt "120020" ]] ; then BAND=2.5mm
elif [[ $BAND -ge "142000" && $BAND -lt "149000" ]] ; then BAND=2mm
elif [[ $BAND -ge "241000" && $BAND -lt "250000" ]] ; then BAND=1mm
else
     echo "Could not match a valid band. Skipping record."
     exit 0
fi

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

ADIF_HRD=$(echo "Callsign=$HRD_USER&Code=$HRD_KEY&App=PY2RAF-QSL&ADIFData=<qso_date:${#QSO_DATE}>$QSO_DATE<time_on:${#QSO_TIME}>$QSO_TIME<call:${#CALLSIGN}>$CALLSIGN<freq:${#QRG}>$QRG<mode:${#MODE}>$MODE<rst_rcvd:${#RST_R}>$RST_R<rst_sent:${#RST_T}>$RST_T<station_callsign:${#MY_CALLSIGN}>$MY_CALLSIGN<stx:${#SERIAL}>$SERIAL<tx_pwr:${#TX_POWER}>$TX_POWER<lotw_qsl_sent:1>Y<EQSL_QSL_SENT:1>Y<qsl_sent:1>Y<qsl_sent_via:1>E<comment:${#EQSLMSG}>$EQSLMSG<band:${#BAND}>$BAND<EOR>")

# Only logs QSO if not a blacklisted QRG
if ! [[ $SKIP_LOG == *$QRG* ]] ; then
   if ! curl -d "$ADIF_QRZ" -X POST https://logbook.qrz.com/api | grep "RESULT=OK" >/dev/null ; then 
      echo "<P>Problemas ao incluir no QRZ</P>"
      echo $ADIF_QRZ >> $QRZ_ERRLOG
   else
      echo "QRZ OK<BR>"
   fi

   if ! curl -d "$ADIF_HRD" -X POST http://robot.hrdlog.net/NewEntry.aspx | grep "<id>" >/dev/null ; then 
      echo "<P>Problemas ao incluir no HRDLog</P>"
      echo $ADIF_HRD >> $HRD_ERRLOG
   else
      echo "HRDLog OK<BR>"
   fi


   if ! curl -d "$ADIF_EQSL" -X POST https://www.eQSL.cc/qslcard/ImportADIF.cfm | grep "Result: 1" >/dev/null ; then 
      echo "<P>Problemas ao incluir no EQSL</P>"
      echo $ADIF_EQSL >> $EQSL_ERRLOG
   else
      echo "eQSL OK<BR>"
   fi
fi

echo "</table>
</body>
</html>"
