# URL Decoder - decodes the HTTP POST
urldecode() {
  echo -e "$(sed 's/+/ /g;s/%\(..\)/\\x\1/g;')"
}

# Generate new QRZ key file for further transactions
qrz_generate_new_key() {
    if ! curl -m 10 -s "https://xmldata.qrz.com/xml/current/?username=$MY_CALLSIGN&password=$QRZ_PASS" | \
         grep -oPm1 "(?<=<Key>)[^<]+" > $QRZ_KEY_FILE ; then
      echo "Error creating QRZ key"
      exit 1
    fi
}

# Lookup for operator in QRZ database
lookup_qrz() {
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
  # Check for directory presence - and fix the lack of it
  if ! [ -d /tmp/qsl ] ; then
    if ! mkdir /tmp/qsl ; then
      echo "Unable to create /tmp/qsl directory"
      exit 1
    fi
  fi

  # If operator is not present in Labre database, lookup in QRZ.
  #### COMMENTED OUT SINCE LABRE DB IS OUT OF SERVICE
  #if ! lookup_labre $1 ; then
    lookup_qrz $1
  #fi

  # Looks for Bur* in QRZs qslmgr field
  grep -oPm1 "(?<=<qslmgr>)[^<]+" $QRZ_QUERY_FILE | grep -i bur
}
