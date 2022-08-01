#!/bin/bash

rpms=("epel-release" "autoconf" "automake" "bzip2" "bzip2-devel" "cmake" "freetype-devel" "gcc" "gcc-c++" "git" "libtool" "make" "pkgconfig" "zlib-devel")
base_dir='/usr/local/ffmpeg'
src_dir="$base_dir/ffmpeg_sources"
THREADS=$(nproc --all)
FFMPEG_VERSION='4.4.2'

if [ "$EUID" -ne 0 ]
then
    echo "Please run this script as root"
    exit 1
else
    echo "You are root"
fi

rm -rf $base_dir/bin
rm -rf $src_dir
rm -rf $base_dir/ffmpeg_build

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

if [ ! -d $src_dir ] 
then
    echo "Directory $base_dir DOES NOT exists."
    if mkdir -p $src_dir
    then
        echo "Directory $base_dir created"
    else
        echo "ERROR could not create $base_dir"
        exit 1
    fi
else
    echo "Directory exists $base_dir"
fi

export PATH=$base_dir/bin/:$PATH

cd $src_dir
curl -O -L https://www.nasm.us/pub/nasm/releasebuilds/2.15.05/nasm-2.15.05.tar.bz2
tar xjvf nasm-2.15.05.tar.bz2
cd nasm-2.15.05
./autogen.sh
./configure --prefix="$base_dir/ffmpeg_build" --bindir="$base_dir/bin"
make -j $THREADS
make install


cd $src_dir
curl -O -L https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz
tar xzvf yasm-1.3.0.tar.gz
cd yasm-1.3.0
./configure --prefix="$base_dir/ffmpeg_build" --bindir="$base_dir/bin"
make -j $THREADS
make install


cd $src_dir
git clone --branch stable --depth 1 https://code.videolan.org/videolan/x264.git
cd x264
PKG_CONFIG_PATH="$base_dir/ffmpeg_build/lib/pkgconfig" ./configure --prefix="$base_dir/ffmpeg_build" --bindir="$base_dir/bin" --enable-static
make -j $THREADS
make install


cd $src_dir
git clone --depth 1 https://github.com/mstorsjo/fdk-aac
cd fdk-aac
autoreconf -fiv
./configure --prefix="$base_dir/ffmpeg_build" --disable-shared
make -j $THREADS
make install


cd $src_dir
curl -O -L http://ffmpeg.org/releases/ffmpeg-$FFMPEG_VERSION.tar.bz2
tar xjvf ffmpeg-$FFMPEG_VERSION.tar.bz2
cd ffmpeg-$FFMPEG_VERSION
PATH="$base_dir/bin:$PATH" PKG_CONFIG_PATH="$base_dir/ffmpeg_build/lib/pkgconfig" ./configure \
  --prefix="$base_dir/ffmpeg_build" \
  --pkg-config-flags="--static" \
  --extra-cflags="-I$base_dir/ffmpeg_build/include" \
  --extra-ldflags="-L$base_dir/ffmpeg_build/lib" \
  --extra-libs=-lpthread \
  --bindir="$base_dir/bin" \
  --enable-gpl \
  --enable-libx264 \
  --enable-libfdk_aac \
  --enable-nonfree
make -j $THREADS
make install
hash -r

ln -s $base_dir/bin/ffmpeg /usr/local/bin/
ln -s $base_dir/bin/ffprobe /usr/local/bin/