# qso-web
## A simple web-UI CGI-based for logging your QSOs

This is a Shell-Script, web-based QSO logging tool.

It features automatic QRZ, eQSL, ClubLog and HRDLog automatic contact upload, as well configurable skip-frequencies, where you don't want the records logged.

The access control is provided by the `.htaccess` policy file to the `registra.cgi` CGI file, which actually writes the new records.

## Samples

### Log record form:
[PY2RAF Record form](https://rf01.co:8443/q/registro.html)

### QSO list:
[PY2RAF QSO List](https://rf01.co:8443/cgi-bin/lista-qso.cgi)
