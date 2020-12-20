#!/bin/bash

echo "Content-type: text/html"
echo ""

source /etc/qso/qso.conf

##### BUREAU CHECKER
# Verifica se tem requisitos basicos
if ! [ -d /tmp/qsl ] ; then
  if ! mkdir /tmp/qsl ; then
    echo "Unable to create /tmp/qsl directory"
    exit 1
  fi
fi

LISTAGEM_LABRE=/tmp/qsl/listagem-labre.txt
CHAVE_QRZ=$(cat /tmp/qsl/chave_qrz.txt)

checa_indicativo() {
# Se nao existir uma listagem inicial da LABRE, puxa ela.
if ! [ -a $LISTAGEM_LABRE ] ; then
  if ! lynx -dump -connect_timeout=5 -read_timeout=5 \
  http://www.labre-sp.org.br/saa/publico/bureau_online_indicativos.php > $LISTAGEM_LABRE ; then
    echo "Erro recuperando listagem inicial da Labre"
    exit 1
  fi
fi

# Testa se listagem da labre e' atual. Se for mais velha de 1 dia, puxa nova
if [ $(( $(date +%s) - $(stat -c'%Y' $LISTAGEM_LABRE) )) -ge 86400 ] ; then
lynx -dump -connect_timeout=5 -read_timeout=5 \
  http://www.labre-sp.org.br/saa/publico/bureau_online_indicativos.php > /tmp/qsl/listagem-nova.txt
# Testa se listagem nova da LABRE e' atual e correta
  if ! grep $MY_CALL /tmp/qsl/listagem-nova.txt | grep "in use" ; then
    echo "Listagem com problemas, nao atualizei."
    exit 1
  else
    mv /tmp/qsl/listagem-nova.txt $LISTAGEM_LABRE
  fi
fi

# Testa indicativo contra base Labreana SP. Se der positivo; para p/ aqui
if [[ $(grep -w $1 $LISTAGEM_LABRE | grep "in use" | awk '{print $2}') ]] ; then
  echo "Usuario Labreano"
  exit 0
fi

# Pesquisa pelo usuario no QRZ
if ! curl -m 10 -s "https://xmldata.qrz.com/xml/current/?s=$CHAVE_QRZ&callsign=$1" > /tmp/qsl/qrz_query.txt ; then
  echo "Erro consultando QRZ"
  exit 1
fi

# Se na consulta anterior houve problema de chave; gera uma nova
if grep -i error /tmp/qsl/qrz_query.txt ; then 
  if ! curl -m 10 -s "https://xmldata.qrz.com/xml/current/?username=$MY_CALLSIGN&password=$QRZ_PASS" | \
       grep -oPm1 "(?<=<Key>)[^<]+" > /tmp/qsl/chave_qrz.txt ; then
    echo "Erro buscando chave"
    exit 1
  else
# Tenta outra vez consultar, com a chave nova
    CHAVE_QRZ=$(cat /tmp/qsl/chave_qrz.txt)
    if ! curl -m 10 -s "https://xmldata.qrz.com/xml/current/?s=$CHAVE_QRZ&callsign=$1" > /tmp/qsl/qrz_query.txt ; then
      echo "Erro consultando QRZ"
      exit 1
    fi
  fi
fi

# Busca por Bur* no campo qslmgr do QRZ
grep -oPm1 "(?<=<qslmgr>)[^<]+" /tmp/qsl/qrz_query.txt | grep -i bur
}
### END BUREAU CHECKER

# URL Decoder
urldecode() { echo -e "$(sed 's/+/ /g;s/%\(..\)/\\x\1/g;')"; }

read -N $CONTENT_LENGTH QUERY_STRING_POST
QS=($(echo $QUERY_STRING_POST | tr '&' ' '))
CALLSIGN=$(echo ${QS[0]} | awk -F = '{print $2}' | urldecode | tr -dc '[:print:]' | cut -b -15 | tr "[:lower:]" "[:upper:]" )

CONTATOS=$(sqlite -separator ',' $SQDB "SELECT qrg, callsign, op, datetime(qtr,'unixepoch'), obs, mode, power FROM contacts WHERE callsign = '$CALLSIGN' OR op LIKE '%$CALLSIGN%' ORDER BY qtr DESC;" |
           awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td><TD>"$6"</td><TD>"$7"</td></tr>"}')
QTD_CONTATOS=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN'")
CONTATOS_ESTE_ANO=$(sqlite $SQDB "SELECT COUNT(*) FROM contacts WHERE callsign = '$CALLSIGN' AND strftime('%Y',qtr,'unixepoch') = strftime('%Y','now');")

echo "
<html>
<header>
<title>Listagem de contatos - $CALLSIGN</title></header>
<body bgcolor='#ffbd00'>
<h1>Rela&ccedil;&atilde;o de QSOs com <a href=https://www.qrz.com/db/$CALLSIGN>$CALLSIGN</a></h1>"

TZ='America/Sao_Paulo' date ; echo "<P>"

if [[ $QTD_CONTATOS -ge 1 ]] ; then
  QSLS=$(sqlite $SQDB "SELECT COUNT(*) FROM qsl WHERE callsign = '$CALLSIGN'")
  if [[ $QSLS -ge 1 ]] ; then
    echo "<P>QSLs pagos:</P>"
    echo "<table border><tr><td><b>Callsign</td><TD><B>Method</td><td><b>Date</td><td><b>Via</td><td><b>Type</td></tr>"
    sqlite -separator ',' $SQDB "SELECT callsign, method, datetime(date,'unixepoch'), via, type FROM qsl
                             WHERE callsign='$CALLSIGN' ORDER BY date" |
    awk -F , '{print "<tr><TD>"$1"</td><TD>"$2"</td><TD>"$3"</td><TD>"$4"</td><TD>"$5"</td></tr>"}'
    echo "</table>"
  else
    HAS_BUREAU=$(checa_indicativo $CALLSIGN)
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

echo "<table border=1><TR><TD><B>QRG</B></TD><TD><B>Indicativo</B></TD><TD><B>Operador</B></TD><TD><B>QTR</B></td><TD><B>Notas</B></td><TD><B>Modo</B></td><td><b>TXPO</b></td></tr>"

echo "$CONTATOS"

echo "</table>
</body>
</html>"

exit 0
