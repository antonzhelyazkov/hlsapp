# hlsapp
api mp4 to hls

## ffmpeg compile script. Works on Centos7/AlmaLinux8/RockyLimux8
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

```python3-mod_wsgi```

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