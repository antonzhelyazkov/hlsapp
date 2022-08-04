# hlsapp
api mp4 to hls

## ffmpeg compile script. Works on Centos7/AlmaLinux8/RockyLinux8
```-use_localtime_mkdir``` is used to place directory name in chunklist

```
#EXTM3U
#EXT-X-VERSION:6
#EXT-X-TARGETDURATION:4
#EXT-X-MEDIA-SEQUENCE:0
#EXT-X-PLAYLIST-TYPE:VOD
#EXT-X-INDEPENDENT-SEGMENTS
#EXTINF:3.840000,
stream_0/data00.ts
#EXTINF:1.920000,
stream_0/data01.ts
#EXTINF:1.920000,
stream_0/data02.ts
#EXTINF:1.920000,
stream_0/data03.ts
#EXTINF:1.920000,
stream_0/data04.ts
#EXTINF:1.920000,
stream_0/data05.ts
```

```res/ffmpeg_compile.sh```

## install wsgi

```yum instal python3-mod_wsgi```

## install python venv

```
python3 -m venv .venv
source .venv/bin/activate
pip3 install -U pip
pip3 install -r requirements.txt
```

## apache + wsgi setup

```
<VirtualHost *:80>
    ServerAdmin webmaster@flaskhelloworldsite.com
    ServerName helloworld.my.site

    ErrorLog /var/log/httpd/helloworld-error.log
    CustomLog /var/log/httpd/helloworld-access.log combined

    WSGIDaemonProcess hlsapi user=hlsapp group=hlsapp threads=5 python-home=/opt/hlsapp/.venv/ python-path=/opt/hlsapp/
    WSGIProcessGroup hlsapi
    WSGIScriptAlias / /opt/hlsapp/main.py
    <Directory /opt/hlsapp/>
        Require all granted
    </Directory>

</VirtualHost>
```

## apache + HLS

```
<VirtualHost *:80>
    ServerName hls.my.site

    DocumentRoot /var/www/v1/

    ErrorLog /var/log/httpd/v1-error.log
    CustomLog /var/log/httpd/v1-access.log combined

    Header set Access-Control-Allow-Origin "*"

RewriteEngine on
RewriteCond %{SERVER_NAME} =hls.my.site
RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>

<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName hls.my.site

    DocumentRoot /var/www/v1/

    ErrorLog /var/log/httpd/v1-error.log
    CustomLog /var/log/httpd/v1-access.log combined

    Header set Access-Control-Allow-Origin "*"

SSLCertificateFile /etc/letsencrypt/live/hls.my.site/cert.pem
SSLCertificateKeyFile /etc/letsencrypt/live/hls.my.site/privkey.pem
Include /etc/letsencrypt/options-ssl-apache.conf
SSLCertificateChainFile /etc/letsencrypt/live/hls.my.site/chain.pem
</VirtualHost>
</IfModule>
```