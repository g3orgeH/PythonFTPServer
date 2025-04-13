requires Valid cert files as listed bellow

cert.pem
key.pem



These can be generated on a linux machine using the following command
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out cert.pem

For demonstration purposes the username is admin and password is admin on the login screen for the web portal

The webserver url should be displayed on the CLI, the port for the ftp server is 2121, and the webserver is running on https.

And you must create the directory FTP_ROOT, or define a new directory from the home direcotry option in the admin panel.

FTP server Direcotry lsiting will only show data which is stored int FTP_ROOT