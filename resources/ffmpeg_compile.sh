#!/bin/bash

rpms=("epel-release" "autoconf" "automake" "bzip2" "bzip2-devel" "cmake" "freetype-devel" "gcc" "gcc-c++" "git" "libtool" "make" "pkgconfig" "zlib-devel")

for rpm in ${rpms[@]}
do
    if rpm -q --quiet $rpm
    then 
        echo $rpm "alredy installed"
    else
        echo "install $rpm"
        yum install -y $rpm
    fi
done