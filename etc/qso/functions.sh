# URL Decoder - decodes the HTTP POST
urldecode() {
  echo -e "$(sed 's/+/ /g;s/%\(..\)/\\x\1/g;')"
}

# Generate new QRZ key file for further transactions
qrz_generate_new_key() {
  # Check for directory structure - and fix the lack of it
  if ! [ -d /tmp/qsl ] ; then
    if ! mkdir /tmp/qsl ; then
      echo "Unable to create /tmp/qsl directory"
      exit 1
    fi
  fi

  # Create new QRZ key
  if ! curl -m 10 -s "https://xmldata.qrz.com/xml/current/?username=$MY_CALLSIGN&password=$QRZ_PASS" | \
     grep -oPm1 "(?<=<Key>)[^<]+" > $QRZ_KEY_FILE ; then
     echo "Error creating QRZ key"
     exit 1
  fi
}

# Lookup for operator in QRZ database
lookup_qrz() {
  # Only proceed if is there a valid QRZ subscription
  if [[ -z $QRZ_KEY ]] ; then
     echo "No QRZ subscription"
     exit 1
  fi

  # Lookup for a key file. If doesnt exist, create a new one
  if ! [ -e $QRZ_KEY_FILE ] ; then
    qrz_generate_new_key
  fi

  QRZ_XML_KEY=$(cat $QRZ_KEY_FILE)

  if ! curl -m 10 -s "https://xmldata.qrz.com/xml/current/?s=$QRZ_XML_KEY&callsign=$1" > $QRZ_QUERY_FILE ; then
    echo "Error consulting QRZ"
    exit 1
  fi

  # If there was an error (probably bad key) when looking up the callsign, 
  # generate a new key and try again
  if grep -i error $QRZ_QUERY_FILE ; then
    qrz_generate_new_key
    QRZ_XML_KEY=$(cat $QRZ_KEY_FILE)
    if ! curl -m 10 -s "https://xmldata.qrz.com/xml/current/?s=$QRZ_XML_KEY&callsign=$1" > $QRZ_QUERY_FILE ; then
      echo "Error consulting QRZ"
      exit 1
    fi
  fi
}

# Lookup for operator in brazilian LABRE database
lookup_labre() {
  LISTAGEM_LABRE=/tmp/qsl/listagem-labre.txt

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
    if ! grep $MY_CALLSIGN /tmp/qsl/listagem-nova.txt | grep "in use" >/dev/null ; then
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
  else
    exit 1
  fi
}

# Bureau Checker
check_bureau() {
  # If operator is not present in Labre database, lookup in QRZ.
  #### COMMENTED OUT SINCE LABRE DB IS OUT OF SERVICE
  #if ! lookup_labre $1 ; then
    lookup_qrz $1
  #fi

  # Looks for Bur* in QRZs qslmgr field
  grep -oPm1 "(?<=<qslmgr>)[^<]+" $QRZ_QUERY_FILE | grep -i bur
}

get_band() {
FREQ_TEST=$(echo $1 | awk -F . '{print $1}')
if   [[ $FREQ_TEST == "1" ]] ; then echo "160m"
elif [[ $FREQ_TEST == "3" ]] ; then echo "80m"
elif [[ $FREQ_TEST == "5" ]] ; then echo "60m"
elif [[ $FREQ_TEST == "7" ]] ; then echo "40m"
elif [[ $FREQ_TEST == "10" ]] ; then echo "30m"
elif [[ $FREQ_TEST == "14" ]] ; then echo "20m"
elif [[ $FREQ_TEST == "18" ]] ; then echo "17m"
elif [[ $FREQ_TEST == "21" ]] ; then echo "15m"
elif [[ $FREQ_TEST == "24" ]] ; then echo "12m"
elif [[ $FREQ_TEST -ge "28" && $FREQ_TEST -lt "30" ]] ; then echo "10m"
elif [[ $FREQ_TEST -ge "50" && $FREQ_TEST -lt "54" ]] ; then echo "6m"
elif [[ $FREQ_TEST -ge "144" && $FREQ_TEST -lt "148" ]] ; then echo "2m"
elif [[ $FREQ_TEST -ge "222" && $FREQ_TEST -lt "225" ]] ; then echo "1.25m"
elif [[ $FREQ_TEST -ge "420" && $FREQ_TEST -lt "450" ]] ; then echo "70cm"
elif [[ $FREQ_TEST -ge "902" && $FREQ_TEST -lt "928" ]] ; then echo "33cm"
elif [[ $FREQ_TEST -ge "1240" && $FREQ_TEST -lt "1300" ]] ; then echo "23cm"
elif [[ $FREQ_TEST -ge "2300" && $FREQ_TEST -lt "2450" ]] ; then echo "13cm"
elif [[ $FREQ_TEST -ge "3300" && $FREQ_TEST -lt "3500" ]] ; then echo "9cm"
elif [[ $FREQ_TEST -ge "5650" && $FREQ_TEST -lt "5925" ]] ; then echo "6cm"
elif [[ $FREQ_TEST -ge "10000" && $FREQ_TEST -lt "10500" ]] ; then echo "3cm"
elif [[ $FREQ_TEST -ge "24000" && $FREQ_TEST -lt "24250" ]] ; then echo "1.25cm"
elif [[ $FREQ_TEST -ge "47000" && $FREQ_TEST -lt "47200" ]] ; then echo "6mm"
elif [[ $FREQ_TEST -ge "75500" && $FREQ_TEST -lt "81000" ]] ; then echo "4mm"
elif [[ $FREQ_TEST -ge "119980" && $FREQ_TEST -lt "120020" ]] ; then echo "2.5mm"
elif [[ $FREQ_TEST -ge "142000" && $FREQ_TEST -lt "149000" ]] ; then echo "2mm"
elif [[ $FREQ_TEST -ge "241000" && $FREQ_TEST -lt "250000" ]] ; then echo "1mm"
else
     echo "Could not match a valid band. Skipping record."
     return 1
fi
}
