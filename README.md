# qso-web
## A simple web-UI CGI-based for logging your QSOs

This is a Shell-Script, web-based QSO logging tool.

It features:
* Instantaneous and automatic LOTW, QRZ, eQSL, ClubLog and HRDLog contact upload
* QSL card control
* Looks up for Bureau acceptance in QRZ (requires QRZ subscription)
* Allows skip-frequencies, where you don't want the records logged.

The access control is provided by the `.htaccess` policy file to the `registra.cgi` CGI file, which actually writes the new records.

## A word about LOTW.
### Motivation
The ARRL's Logbook of the World (LOTW) cannonical tool for handling contacts is the TQSL tool.
While TQSL is [open source](http://www.arrl.org/tqsl-download), I was not exactly fond of the idea for using it for interfacing with my logging system - it's a powerful tool with several other extra functionalities (which I was not interested for logging sake) and I wanted something super slim and straightforward - Thus I moved to my own implementation of TQSL.
In my TQSL's implementation, the main goal is to automatically log to LOTW all of my contacts at the time of the QSO, without having TQSL installed.

### Implementation
#### ~~Planes, trains and automobiles~~ Certificates, Keys and TQSL

##### TQ6 file
Your certificate lies in a `.tq6` file - Which is a GZip'ed file containing the certificate trust chain, from the CA to your certificate (in clause `<usercert>`) and the TQSL schema for entities, modes, etc.

~~~
[rfreire@rf rpmbuild]$ file lotw.tq6 
lotw.tq6: gzip compressed data, from Unix

[rfreire@rf rpmbuild]$ gunzip -S .tq6 lotw.tq6
<?xml version="1.0" encoding="UTF-8" ?>
<tqsldata>
   <tqslcerts>
      <rootcert>-----BEGIN CERTIFICATE-----
[...]
~~~

##### p12 file
By using your TQSL utility you can export a `.p12` file containing a signing key. In the Callsign Certificate, use the option `Save the callsign certificate for <YOUR CALLSIGN>`.

First, extract your User Certificate from the `.p12` file, it is the first certificate in the chain and save it to `lotw-<callsign>.cer`

~~~
[rfreire@rf rpmbuild]$ openssl pkcs12 -info -in lotw.p12 
Enter Import Password:
MAC Iteration 2048
MAC verified OK
PKCS7 Encrypted data: pbeWithSHA1And40BitRC2-CBC, Iteration 2048
Certificate bag
Bag Attributes
    localKeyID: CC AC 6E 08 94 09 6E 7E B7 5B 2E 90 1A 24 2E CE 10 07 35 5D 
    friendlyName: TrustedQSL user certificate
subject=/1.3.6.1.4.1.12348.1.1=PY2RAF/CN=Rodrigo A B Freire/emailAddress=py2raf@rf3.org
issuer=/C=US/ST=CT/L=Newington/O=American Radio Relay League/OU=Logbook of the World/CN=Logbook of the World Production CA/DC=arrl.org/emailAddress=lotw@arrl.org
-----BEGIN CERTIFICATE-----
MIIEtTCCA52gAwIBAgIDBw2TMA0GCSqGSIb3DQEBCwUAMIHYMQswCQYDVQQGEwJV
UzELMAkGA1UECAwCQ1QxEjAQBgNVBAcMCU5ld2luZ3RvbjEkMCIGA1UECgwbQW1l
[...]
~~~

And now, get the private key to be able to sign content using this certificate. Give it a password in `Enter PEM pass phrase` step, otherwise it will fail miserably whining about the lack of a password. Save it as `lotw-<callsign>.key`

~~~
[rfreire@rf rpmbuild]$ openssl pkcs12 -in lotw.p12 -nocerts -out lotw-<callsign>.key
Enter Import Password:
MAC verified OK
Enter PEM pass phrase:
Verifying - Enter PEM pass phrase:
~~~

Now, you have obtained all you need to do sign the contacts.

#### The TQ8 (contact) file
The `.tq8` file actually contains the contacts to be uploaded to the LOTW. It is a gzip-compressed file and with a characteristic structure which I'll share below. Won't go into details, as the details are pretty much self-described.

The highlights of the `tq8` file are:

##### Static content
* The header
* Your certificate
* Your station id and location information
* Your contact

##### Variable content
The contact information. Namely:
* Callsign
* Band
* Mode
* Frequency
* Date
* Time
* The data hash/signature
* The data that was used to calc the hash/signature

~~~
[rfreire@rf rpmbuild]$ file py2raf.tq8
py2raf.tq8: gzip compressed data, was "py2raf", from Unix, last modified: Tue Dec 31 13:27:43 2019

[rfreire@rf rpmbuild]$ gunzip -S .tq8 py2raf.tq8

[rfreire@rf rpmbuild]$ cat py2raf
<TQSL_IDENT:53>TQSL V2.5.1 Lib: V2.5 Config: V11.9 AllowDupes: false

<Rec_Type:5>tCERT
<CERT_UID:1>1
<CERTIFICATE:1638>MIIEtTCCA52gAwIBAgIDBw2TMA0GCSqGSIb3DQEBCwUAMIHYMQswCQYDVQQGEwJV
UzELMAkGA1UECAwCQ1QxEjAQBgNVBAcMCU5ld2luZ3RvbjEkMCIGA1UECgwbQW1l
[...]
zQf9UWPErprv
<eor>

<Rec_Type:8>tSTATION
<STATION_UID:1>1
<CERT_UID:1>1
<CALL:6>PY2RAF
<DXCC:3>108
<GRIDSQUARE:6>GG66gm
<ITUZ:2>15
<CQZ:2>11
<eor>

<Rec_Type:8>tCONTACT
<STATION_UID:1>1
<CALL:5>PY2XX
<BAND:4>70CM
<MODE:3>FAX
<FREQ:7>439.480
<QSO_DATE:10>2019-12-31
<QSO_TIME:9>10:00:00Z
<SIGN_LOTW_V2.0:175:6>cLO9toAVzpzhDjMlMuJHAS7z6Tjpq95U0yvpd2qawz7tIrUG6jXUq9RHy4yuZd2x
kwDIkIyjv6iMevwDfFeETP0XjHQziRiUC1Ol6YnCBl3GWQAX05Y8OxEpUx0fy6Tu
8osQlV7rJ0YtvNmhPc/Fz7w79JdXqM2KVIxyUsy6tzM=
<SIGNDATA:48>11GG66GM1570CMPY2XX439.480FAX2019-12-3110:00:00Z
<eor>
~~~

The data to be signed is defined in the following order, with no spaces:
* Your CQ Zone
* Your GRID
* Your ITU Zone
* Contact's BAND
* Contact's CALLSIGN
* Frequency
* Mode
* QSO Date (has strict format)
* QSO Time (has strict format)

#### Signing the content
After you built the string to be hashed/signed, then sign it with your key. See the below sample:

~~~
$ echo $STRING-TO-BE-SIGNED | openssl dgst -sha1 -sign lotw-py2raf.key -passin 'pass:<password>' | base64
~~~

Pronto. Now you have prepared the signed content and the last step is build the file containing all the required fields, compact it, and upload to LOTW.

#### Uploading to LOTW
See the below sample curl

~~~
$ curl -F 'upfile=@lotw-PY2RAF.tq8' https://lotw.arrl.org/lotw/upload
~~~

## SQLite notes.

Now outputs log to SQLite too. Schema:

~~~
CREATE TABLE contacts ( 
  serial INTEGER PRIMARY KEY, 
  qrg REAL, 
  callsign TEXT, 
  op TEXT, 
  qtr INTEGER, 
  mode TEXT, 
  power INTEGER, 
  propagation TEXT, 
  sighis INTEGER, 
  sigmy INTEGER, 
  qth TEXT, 
  obs TEXT );
~~~

QSL Schema:

~~~
CREATE TABLE qsl (
  callsign TEXT, 
  method TEXT, 
  date INTEGER, 
  via TEXT, 
  type TEXT, 
  xo BOOLEAN );
~~~

Caveat: Your web user must have read/write permission not only to the sqlite file, but to your sqlite **directory** too - Otherwise, it will spew a Access Denied.

## Sample UI

### Log record form:
[PY2RAF Record form](https://rf3.org:8443/q/registro.html)

### QSO list:
[PY2RAF QSO List](https://rf3.org:8443/cgi-bin/lista-qso.cgi)

![;-)](https://rf3.org:8443/q/wink-qso.png)
