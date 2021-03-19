# Install Browser, OS dependencies and Python modules
FROM public.ecr.aws/lambda/python:3.8 as lambda-base

COPY requirements.txt /tmp/
COPY install-browsers.sh /tmp/

# Install dependencies
RUN yum install xz atk cups-libs gtk3 libXcomposite alsa-lib tar \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel unzip bzip2 -y -q

# Install Browsers
RUN /usr/bin/bash /tmp/install-browsers.sh

# Install Python dependencies for function
RUN pip install --upgrade pip -q
RUN pip install -r /tmp/requirements.txt -q

# Remove not needed packages
RUN yum remove xz tar unzip bzip2 -y

# Build FFmpeg
FROM public.ecr.aws/lambda/python:3.8 as ffmpeg
WORKDIR /ffmpeg_sources
RUN yum install autoconf automake bzip2 bzip2-devel cmake libxcb libxcb-devel \
    freetype-devel gcc gcc-c++ git libtool make pkgconfig zlib-devel -y -q

# Compile NASM assembler
RUN curl -OL https://www.nasm.us/pub/nasm/releasebuilds/2.15.05/nasm-2.15.05.tar.bz2
RUN tar xjvf nasm-2.15.05.tar.bz2
RUN cd nasm-2.15.05 && sh autogen.sh && \
    ./configure --prefix="/ffmpeg_sources/ffmpeg_build" \
    --bindir="/ffmpeg_sources/bin" && \
    make && make install

# Compile Yasm assembler
RUN curl -OL https://www.tortall.net/projects/yasm/releases/yasm-1.3.0.tar.gz
RUN tar xzvf yasm-1.3.0.tar.gz
RUN cd yasm-1.3.0 && \
    ./configure --prefix="/ffmpeg_sources/ffmpeg_build" \
    --bindir="/ffmpeg_sources/bin" && \
    make && make install

# Compile FFmpeg
RUN curl -OL https://ffmpeg.org/releases/ffmpeg-snapshot.tar.bz2
RUN tar xjvf ffmpeg-snapshot.tar.bz2
RUN cd ffmpeg && \
    export PATH="/ffmpeg_sources/bin:$PATH" && \
    export PKG_CONFIG_PATH="/ffmpeg_sources/ffmpeg_build/lib/pkgconfig" && \
    ./configure \
    --prefix="/ffmpeg_sources/ffmpeg_build" \
    --pkg-config-flags="--static" \
    --extra-cflags="-I/ffmpeg_sources/ffmpeg_build/include" \
    --extra-ldflags="-L/ffmpeg_sources/ffmpeg_build/lib" \
    --extra-libs=-lpthread \
    --extra-libs=-lm \
    --enable-libxcb \
    --bindir="/ffmpeg_sources/bin" && \
    make && \
    make install


# Final image with code and dependencies
FROM lambda-base 

# Copy FFMpeg binary
COPY --from=ffmpeg /ffmpeg_sources/bin/ffmpeg /usr/bin/

# # Copy function code
COPY app.py /var/task/
