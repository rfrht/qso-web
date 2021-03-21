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

# Read the form POST and sanitize it
read -N $CONTENT_LENGTH QUERY_STRING_POST
QS=($(echo $QUERY_STRING_POST | tr '&' ' '))
QRG=$(echo ${QS[3]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -8 )
CALLSIGN=$(echo ${QS[0]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -15 )
OP=$(echo ${QS[1]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 )
QTH=$(echo ${QS[2]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -40 )
TX_POWER=$(echo ${QS[4]} | awk -F = '{print $2}' | tr -dc '[:digit:]' | cut -b -3 )
MODE=$(echo ${QS[5]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 )
SIG_MY=$(echo ${QS[6]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 )
SIG_HIS=$(echo ${QS[7]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -18 )
ALT_D=$(echo ${QS[8]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -11 )
ALT_T=$(echo ${QS[9]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -5 ) 
CONTEST_ID=$(echo ${QS[10]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -25 )
OBS=$(echo ${QS[11]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -40 )
BUTTON=$(echo ${QS[12]^^} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -10 )

# Was the QRZ button pressed? If it is, QRZ it.
if [ "$BUTTON" == "QRZ" ] ; then

  lookup_qrz $CALLSIGN

  OP=$(grep -oPm1 "(?<=<fname>)[^<]+" $QRZ_QUERY_FILE | tr -dc '[:alnum:] [:space:]' )
  QTH=$(grep -oPm1 "(?<=<addr2>)[^<]+" $QRZ_QUERY_FILE | tr -dc '[:alnum:] [:space:]' )
  cat $RECORD_FORM | sed -e "/Watt/d" \
                         -e "s/\"$MODE\"/\"$MODE\" checked/g" \
                         -e "s/\"F1f/$QRG\"/g" \
                         -e "s/\"F2f/$TX_POWER\"/g" \
                         -e "s/\"F3f/$CONTEST_ID\"/g" \
                         -e "s/\"F4f/$CALLSIGN\"/g" \
                         -e "s/\"F5f autofocus/\" value=\"$CALLSIGN\"/g" \
                         -e "s/F6f/ value=\"$OP\"/g" \
                         -e "s/\"F7f/$CALLSIGN\"/g" \
                         -e "s/\"F8f/$QTH\"/g" \
                         -e "s/F9f/ autofocus/g"
  exit 0

# No callsign, no op name, no contest ID - this is a lookup request.
elif [[ -n $CALLSIGN && -z $OP && -z $CONTEST_ID ]] ; then
  QTD_CONTATOS=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN'")
  CONTATOS_ESTE_ANO=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN' 
                                  AND strftime('%Y',qtr,'unixepoch') = strftime('%Y','now');")

  if [[ $QTD_CONTATOS -ge 1 ]] ; then
    QSLS=$(sqlite $SQDB "SELECT COUNT(*) FROM qsl WHERE callsign = '$CALLSIGN'")
    OP=$(sqlite $SQDB "SELECT op FROM contacts WHERE callsign = '$CALLSIGN' ORDER BY serial DESC LIMIT 1")
    QTH=$(sqlite $SQDB "SELECT qth FROM contacts WHERE callsign = '$CALLSIGN' ORDER BY serial DESC LIMIT 1")

    if [ -z "$MODE" ] ; then MODE="FM" ; fi
    cat $RECORD_FORM | sed -e "/Watt/d" \
                           -e "s/\"$MODE\"/\"$MODE\" checked/g" \
                           -e "s/\"F1f/$QRG\"/g" \
                           -e "s/\"F2f/$TX_POWER\"/g" \
                           -e "s/\"F3f/$CONTEST_ID\"/g" \
                           -e "s/\"F4f/$CALLSIGN\"/g" \
                           -e "s/\"F5f autofocus/\" value=\"$CALLSIGN\"/g" \
                           -e "s/F6f/ value=\"$OP\"/g" \
                           -e "s/\"F7f/$CALLSIGN\"/g" \
                           -e "s/\"F8f/$QTH\"/g" \
                           -e "s/F9f/ autofocus/g"

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

    echo "<h2>Contatos: $QTD_CONTATOS</h2>
          <h3>Este ano: $CONTATOS_ESTE_ANO</h3>"

    echo "<table border><tr><td><b>QRG (MHz)</td><TD><B>Indicativo</td><td><b>Operador</td><td><b>QTR (GMT)</td><td><b>QTH</td><td><b>Modo</td><td><b>Serial</td><TD><B>Watts</b></td><TD><B>ObS</b></td><TD><B>His Sig</b></td><TD><B>My Sig</b></td></tr>"
    sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), qth, mode, serial, power, obs, sighis, sigmy 
                                 FROM contacts WHERE callsign = '$CALLSIGN' OR op LIKE '%$CALLSIGN%' 
                                 ORDER BY qtr DESC;" |
    awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td><TD>"$9"</td><TD>"$10"</td><TD>"$11"</td></tr>"}'

    echo "</table>
<!-- QRZ Log Block -->
<P><iframe align=\"top\" frameborder=\"0\" height=\"520\" scrolling=\"yes\" src=\"https://logbook.qrz.com/lbstat/$MY_CALLSIGN/\" width=\"800\"></iframe>
</body>
</html>"

    exit 0
  fi

  if [ -z "$MODE" ] ; then MODE="FM" ; fi

  cat $RECORD_FORM | sed -e "/Watt/d" \
                         -e "s/\"$MODE\"/\"$MODE\" checked/g" \
                         -e "s/\"F1f/$QRG\"/g" \
                         -e "s/\"F2f/$TX_POWER\"/g" \
                         -e "s/\"F3f/$CONTEST_ID\"/g" \
                         -e "s/\"F4f/$CALLSIGN\"/g" \
                         -e "s/\"F5f autofocus/\" value=\"$CALLSIGN\"/g" \
                         -e "s/F6f/ autofocus/g" \
                         -e "s/\"F7f/$CALLSIGN\"/g"
  echo "<table border><tr><td><b>QRG (MHz)</td><TD><B>Indicativo</td><td><b>Operador</td><td><b>QTR (GMT)</td><td><b>QTH</td><td><b>Modo</td><td><b>Serial</td><TD><B>Watts</b></td><TD><B>Obs.:</b></td><TD><B>His Sig</b></td><TD><B>My Sig</b></td></tr>"
  sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), qth, mode, serial, power, obs, sighis, sigmy 
                               FROM contacts WHERE op LIKE '%$CALLSIGN%' ORDER BY qtr DESC;" |
  awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td><TD>"$9"</td><TD>"$10"</td><TD>"$11"</td></tr>"}'
  echo "</table>"
  exit 0
fi

# Bail if no proper mode is selected
if [ $MODE == "RST" ] ; then echo "Selecione modo" ; exit 1 ; fi

# Check for impossible power modes
if [[ $TX_POWER -lt 5 || $TX_POWER -gt 100 ]] ; then echo "Check Power - outside nominals" ; exit 1 ; fi

# My transceiver is only capable of 40W in AM mode
# Fails if logging more than 40W in AM
if [[ $TX_POWER -gt 40 && $MODE == "AM" ]] ; then echo "Mais de 40W em AM?" ; exit 1 ; fi

# Prepare the QSO date.
if [[ -n $ALT_D && -n $ALT_T ]] ; then
   EPOCH=$(TZ=UTC date +%s --date="$ALT_D $ALT_T:00")
else
   EPOCH=$(TZ=UTC date +%s)
fi

if [ -z $EPOCH ] ; then echo "Erro de Data" ; exit 1 ; fi

QTR=$(TZ=UTC date +%c --date="@$EPOCH")
QSO_DATE=$(TZ=UTC date +%Y%m%d --date="@$EPOCH")
QSO_TIME=$(TZ=UTC date +%H%M --date="@$EPOCH")

# Calculate serial number
SERIAL=$(/usr/bin/sqlite $SQDB "SELECT MAX(serial)+1 FROM contacts;")
if ! [[ $SERIAL -ge 1 ]] ; then SERIAL=1 ; fi

# Identify where I'm transmitting from. Sao Paulo or Votorantim
if [[ ! $REMOTE_ADDR =~ "172.16." ]] ; then
   GRID=$ALT_GRID
   OBS="TX $ALT_GRID $OBS"
   ANTENNA_HF="$ALT_ANTENNA_HF"
   ANTENNA_VHF_UHF="$ALT_ANTENNA_VHF_UHF"
fi

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

# Detect wrong mode - if adding the "+" or "-", infer it's FT8.
# But make an exception for JT65.
if [[ $MODE != "JT65" ]]; then
  if [[ $SIG_MY =~ "+" || $SIG_MY =~ "-" ]] || [[ $SIG_HIS =~ "+" || $SIG_HIS =~ "-" ]] && [[ $MODE != "WSPR" ]] ; then
     MODE=FT8
  fi
fi

# Calculate propagation mode
FREQKC=$(echo $QRG | tr -dc '[:digit:]')
# Repeaters
if [[ $FREQKC -ge 145200 && $FREQKC -le 145500 ]] ||
   [[ $FREQKC -ge 146600 && $FREQKC -le 147400 ]]
then
   PROP_MODE="RPT"
fi

# My transceiver is only capable of 50W in VHF and UHF
# Fails if logging more than 50W V/UHF
if [[ $TX_POWER -gt 50 && $FREQKC -ge 144000 ]] ; then echo "Mais de 50W em V/U?" ; exit 1 ; fi

# Proper antenna selection
if [[ $BAND == "2m" || $BAND == "70cm" ]] ; then
   ANTENNA=$ANTENNA_VHF_UHF
else
   ANTENNA=$ANTENNA_HF
fi

# Stop logging if missing essential fields
if [[ -z $QRG || -z $CALLSIGN || -z $MODE ]] || 
   [[ ( -z $SIG_MY || -z $SIG_HIS ) && $MODE == "FT8" ]]
then
   echo "<h1>FALTOU CAMPO ESSENCIAL</h1>"
   # Reuse this QSO data in new contact form
   cat $RECORD_FORM | sed -e "s/\"Ff/$QRG\"/g" -e "s/\"$MODE\"/\"$MODE\" checked/g" -e "s/\"15\"/\"$TX_POWER\"/g"
   exit 0
# Avoids logging FM contacts in HF frequencies
elif [[ $FREQKC -lt "29000" && $MODE == "FM" ]] ; then
   echo "<h1>FM em HF?</h1>"
   # Reuse this QSO data in new contact form
   cat $RECORD_FORM | sed -e "s/\"Ff/$QRG\"/g" -e "s/\"$MODE\"/\"$MODE\" checked/g" -e "s/\"15\"/\"$TX_POWER\"/g"
   exit 0
# Avoids logging SSB contacts in high 2m frequencies
elif [[ $FREQKC -gt "144800" && $FREQKC -lt "148000" && $MODE == "SSB" ]] ; then
   echo "<h1>SSB em 2m?</h1>"
   # Reuse this QSO data in new contact form
   cat $RECORD_FORM | sed -e "s/\"Ff/$QRG\"/g" -e "s/\"$MODE\"/\"$MODE\" checked/g" -e "s/\"15\"/\"$TX_POWER\"/g"
   exit 0
fi

# Prepare the notes field, if the RST was provided or not.
## Special sauce for WSPR
if [ $MODE == "WSPR" ] ; then
   # Requires remote Received signal and power at 5W (FT-991A minimum TX Power)
   if ! [[ -z $SIG_MY && -n $SIG_HIS ]] && [[ $TX_POWER == 5 ]] ; then
      echo "<H1>PREENCHIMENTO INCORRETO</H1>"
      exit 1
   fi
elif [ ! -z "$CONTEST_ID" ] ; then
   OBS=$(echo "$CONTEST_ID // $QTH")
   SIG_MY=59
   SIG_HIS=59
## Special sauce for FT8
elif [ $MODE == "FT8" ] ; then
   # Avoid FT8 logs with more than 25 dB; probably on error
   if [[ $SIG_MY -ge 25 || $SIG_HIS -ge 25 ]] ; then
      echo "<h1>MAIS DE 25 dB EM FT8???</h1>"
      exit 1
   fi
fi

# Reuse fields from this QSO to the next one
cat $RECORD_FORM | sed -e "s/\"F1f/$QRG\"/g" \
                       -e "s/\"$MODE\"/\"$MODE\" checked/g" \
                       -e "s/\"F2f/$TX_POWER\"/g" \
                       -e "s/\"F3f/$CONTEST_ID\"/g" \
                       -e "s/\"F4f/$CALLSIGN\"/g"

# ===== 3RD PARTY SYSTEM LOG - String prep =====
# QRZ
ADIF_QRZ=$(echo "KEY=$QRZ_KEY&ACTION=INSERT&ADIF=<freq:${#QRG}>$QRG<mode:${#MODE}>$MODE<qso_date:${#QSO_DATE}>$QSO_DATE<call:${#CALLSIGN}>$CALLSIGN<time_on:${#QSO_TIME}>$QSO_TIME<comment:${#QTH}>$QTH<station_callsign:${#MY_CALLSIGN}>$MY_CALLSIGN<stx:${#SERIAL}>$SERIAL<tx_pwr:${#TX_POWER}>$TX_POWER<rst_rcvd:${#SIG_MY}>$SIG_MY<rst_sent:${#SIG_HIS}>$SIG_HIS<prop_mode:${#PROP_MODE}>$PROP_MODE<contest_id:${#CONTEST_ID}>$CONTEST_ID<MY_GRIDSQUARE:${#GRID}>$GRID<lotw_qsl_sent:1>Y<EQSL_QSL_SENT:1>Y<qsl_sent:1>Y<eor>")

# ClubLog
ADIF_CLUBLOG=$(echo "email=$CLUBLOG_EMAIL&callsign=$MY_CALLSIGN&api=$CLUBLOG_KEY&password=$CLUBLOG_APP_PASS&adif=<qso_date:${#QSO_DATE}>$QSO_DATE<time_on:${#QSO_TIME}>$QSO_TIME<call:${#CALLSIGN}>$CALLSIGN<freq:${#QRG}>$QRG<mode:${#MODE}>$MODE<rst_rcvd:${#SIG_MY}>$SIG_MY<rst_sent:${#SIG_HIS}>$SIG_HIS<qsl_sent:1>Y<qsl_sent_via:1>E<band:${#BAND}>$BAND<prop_mode:${#PROP_MODE}>$PROP_MODE<contest_id:${#CONTEST_ID}>$CONTEST_ID<MY_GRIDSQUARE:${#GRID}>$GRID<EOR>")

# HRDLog
ADIF_HRD=$(echo "Callsign=$HRD_USER&Code=$HRD_KEY&App=PY2RAF-QSL&ADIFData=<qso_date:${#QSO_DATE}>$QSO_DATE<time_on:${#QSO_TIME}>$QSO_TIME<call:${#CALLSIGN}>$CALLSIGN<freq:${#QRG}>$QRG<mode:${#MODE}>$MODE<rst_rcvd:${#SIG_MY}>$SIG_MY<rst_sent:${#SIG_HIS}>$SIG_HIS<station_callsign:${#MY_CALLSIGN}>$MY_CALLSIGN<stx:${#SERIAL}>$SERIAL<tx_pwr:${#TX_POWER}>$TX_POWER<lotw_qsl_sent:1>Y<EQSL_QSL_SENT:1>Y<qsl_sent:1>Y<qsl_sent_via:1>E<comment:${#EQSLMSG}>$EQSLMSG<band:${#BAND}>$BAND<prop_mode:${#PROP_MODE}>$PROP_MODE<contest_id:${#CONTEST_ID}>$CONTEST_ID<MY_GRIDSQUARE:${#GRID}>$GRID<EOR>")

# EQSL
EQSLMSG="TNX 4 QSO $OP - ANT $ANTENNA - Rig FT-991A - TX $TX_POWER W - SERnr $SERIAL - QRZ/ClubLog/LOTW OK - 73s o/"
ADIF_EQSL=$(echo "ADIFData=PY2RAF QSL upload<ADIF_VER:4>1.00<EQSL_USER:${#EQSL_USER}>$EQSL_USER<EQSL_PSWD:${#EQSL_PASS}>$EQSL_PASS<EOH><freq:${#QRG}>$QRG<mode:${#MODE}>$MODE<qso_date:${#QSO_DATE}>$QSO_DATE<call:${#CALLSIGN}>$CALLSIGN<time_on:${#QSO_TIME}>$QSO_TIME<qslmsg:${#EQSLMSG}>$EQSLMSG<station_callsign:${#MY_CALLSIGN}>$MY_CALLSIGN<stx:${#SERIAL}>$SERIAL<tx_pwr:${#TX_POWER}>$TX_POWER<rst_rcvd:${#SIG_MY}>$SIG_MY<rst_sent:${#SIG_HIS}>$SIG_HIS<prop_mode:${#PROP_MODE}>$PROP_MODE<contest_id:${#CONTEST_ID}>$CONTEST_ID<MY_GRIDSQUARE:${#GRID}>$GRID<eor>")

# LotW
if [[ -n $LOTW_CERT && -n $LOTW_KEY_PASS && -n $LOTW_CQZ && -n $GRID && -n $LOTW_ITUZ && -n $LOTW_KEY && -n $LOTW_DXCC ]] ; then
  LOTW_STRIPPED_CERT=$(grep -v "\-\-\-" $LOTW_CERT)
  LOTW_QSO_DATE=$(TZ=UTC date +%F --date="@$EPOCH")
  LOTW_QSO_QTR=$(TZ=UTC date +%TZ --date="@$EPOCH")
  LOTW_SIGN_DATA=$(echo -n "$LOTW_CQZ$GRID$LOTW_ITUZ$BAND$CALLSIGN$QRG$MODE$LOTW_QSO_DATE$LOTW_QSO_QTR")
  LOTW_SIGNATURE=$(echo -n "$LOTW_SIGN_DATA" | openssl dgst -sha1 -sign $LOTW_KEY -passin "pass:$LOTW_KEY_PASS" | base64)
  ADIF_LOTW=$(echo "<TQSL_IDENT:53>TQSL V2.5.1 Lib: V2.5 Config: V11.9 AllowDupes: false

<Rec_Type:5>tCERT
<CERT_UID:1>1
<CERTIFICATE:${#LOTW_STRIPPED_CERT}>$LOTW_STRIPPED_CERT
<eor>

<Rec_Type:8>tSTATION
<STATION_UID:1>1
<CERT_UID:1>1
<CALL:${#MY_CALLSIGN}>$MY_CALLSIGN
<DXCC:${#LOTW_DXCC}>$LOTW_DXCC
<GRIDSQUARE:${#GRID}>$GRID
<ITUZ:${#LOTW_ITUZ}>$LOTW_ITUZ
<CQZ:${#LOTW_CQZ}>$LOTW_CQZ
<eor>

<Rec_Type:8>tCONTACT
<STATION_UID:1>1
<CALL:${#CALLSIGN}>$CALLSIGN
<BAND:${#BAND}>$BAND
<MODE:${#MODE}>$MODE
<FREQ:${#QRG}>$QRG
<QSO_DATE:${#LOTW_QSO_DATE}>$LOTW_QSO_DATE
<QSO_TIME:${#LOTW_QSO_QTR}>$LOTW_QSO_QTR
<SIGN_LOTW_V2.0:${#LOTW_SIGNATURE}:6>$LOTW_SIGNATURE
<SIGNDATA:${#LOTW_SIGN_DATA}>$LOTW_SIGN_DATA
<eor>
")

  echo "$ADIF_LOTW" > /dev/shm/lotw-$MY_CALLSIGN
  gzip -f -S .tq8 /dev/shm/lotw-$MY_CALLSIGN
fi

if [ $DEBUG == 1 ] ; then
   echo "Modo Debug - Testes escritos"
   echo "$ADIF_QRZ" >> $QRZ_ERRLOG
   echo "$ADIF_CLUBLOG" >> $CLUBLOG_ERRLOG
   echo "$ADIF_HRD" >> $HRD_ERRLOG
   echo "$ADIF_EQSL" >> $EQSL_ERRLOG
   echo "INSERT INTO contacts (qrg, callsign, op, qtr, qth, mode, power, propagation, sighis, sigmy) VALUES ('$QRG','$CALLSIGN','$OP','$EPOCH','$QTH','$MODE','$TX_POWER','$PROP_MODE','$SIG_MY','$SIG_HIS')" > /dev/shm/transaction-sqlite.log

   sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), qth, mode, serial, power FROM contacts 
                                ORDER BY qtr DESC LIMIT 20" |
   awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td></tr>"}'

   exit 0
fi

# ===== LOG CONTACTS =====
# Log it locally in CSV
if ! echo $QRG,$CALLSIGN,$OP,$QTR,$QTH,$MODE,$SERIAL,$TX_POWER,$PROP_MODE >> $QSO_LOGFILE ; then
   echo "<H1>Error Writing Local Log File $QSO_LOGFILE</h1>"
   exit 1
fi

# Logs the contact in SQLite DB
if [[ -n $SQDB ]] ; then
  if ! /usr/bin/sqlite $SQDB "INSERT INTO contacts (serial, qrg, callsign, op, qtr, qth, mode, power, propagation, sighis, sigmy, obs) VALUES ('$SERIAL','$QRG','$CALLSIGN','$OP','$EPOCH','$QTH','$MODE','$TX_POWER','$PROP_MODE','$SIG_MY','$SIG_HIS','$OBS')" >/dev/shm/transaction-sqlite.log 2>&1; then
    echo "<P>Problemas ao registrar o SQLite</p>"
  else
    echo "SQLite OK<BR>"
  fi
fi

# Show the last 20 after logging the Contact
sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), qth, mode, serial, power, obs, sighis, sigmy FROM contacts 
                             ORDER BY qtr DESC LIMIT 20" |
awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td><TD>"$8"</td><TD>"$9"</td><TD>"$10"</td><TD>"$11"</td></tr>"}'

# Only logs QSOs externally if not a blacklisted QRG
if ! [[ $SKIP_LOG == *$QRG* ]] ; then

## And only logs if clauses are properly populated.
## QRZ
  if [[ -n $QRZ_KEY ]] ; then
   if ! curl -m 30 -d "$ADIF_QRZ" -X POST https://logbook.qrz.com/api | grep "RESULT=OK" >/dev/shm/transaction-qrz.log ; then 
      echo "<P>Problemas ao incluir no QRZ</P>"
      echo $ADIF_QRZ >> $QRZ_ERRLOG
   else
      echo "QRZ OK<BR>"
   fi
  fi

## ClubLog
  if [[ -n $CLUBLOG_EMAIL && -n $CLUBLOG_KEY && -n $CLUBLOG_APP_PASS ]] ; then
   if ! curl -m 30 -kd "$ADIF_CLUBLOG" -X POST https://clublog.org/realtime.php | grep "OK" >/dev/shm/transaction-clublog.log ; then
      echo "<P>Problemas ao incluir no ClubLog</P>"
      echo $ADIF_CLUBLOG >> $CLUBLOG_ERRLOG
   else
      echo "ClubLog OK<BR>"
   fi
  fi

## HRDLog
  if [[ -n $HRD_USER && -n $HRD_KEY ]] ; then
   if ! curl -m 30 -d "$ADIF_HRD" -X POST http://robot.hrdlog.net/NewEntry.aspx | grep "<id>" >/dev/shm/transaction-hrdlog.log ; then 
      echo "<P>Problemas ao incluir no HRDLog</P>"
      echo $ADIF_HRD >> $HRD_ERRLOG
   else
      echo "HRDLog OK<BR>"
   fi
  fi

## EQSL
  if [[ -n $EQSL_USER && -n $EQSL_PASS ]] ; then
   if ! curl -m 30 -d "$ADIF_EQSL" -X POST https://www.eQSL.cc/qslcard/ImportADIF.cfm | grep "Result: 1" >/dev/shm/transaction-eqsl.log ; then 
      echo "<P>Problemas ao incluir no EQSL</P>"
      echo $ADIF_EQSL >> $EQSL_ERRLOG
   else
      echo "eQSL OK<BR>"
   fi
  fi

## LotW
if [[ -n $LOTW_CERT && -n $LOTW_KEY_PASS && -n $LOTW_CQZ && -n $GRID && -n $LOTW_ITUZ && -n $LOTW_KEY && -n $LOTW_DXCC ]] ; then
   if ! curl -m 30 -F "upfile=@/dev/shm/lotw-$MY_CALLSIGN.tq8" https://lotw.arrl.org/lotw/upload | grep -i "file queued for processing" >/dev/shm/transaction-lotw.log ; then
      echo "<P>Problemas ao incluir no LotW</P>"
      mv /dev/shm/lotw-$MY_CALLSIGN.tq8 /dev/shm/failed-lotw-$MY_CALLSIGN-$LOTW_QSO_DATE$LOTW_QSO_QTR.tq8
    else
      echo "LotW OK<BR>"
    fi
   fi

fi

echo "</table>

<!-- QRZ Log Block -->
<P><iframe align=\"top\" frameborder=\"0\" height=\"520\" scrolling=\"yes\" src=\"https://logbook.qrz.com/lbstat/$MY_CALLSIGN/\" width=\"800\"></iframe>

</body>
</html>"
