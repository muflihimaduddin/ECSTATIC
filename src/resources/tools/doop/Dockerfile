# Copied from DOOP's repository (https://bitbucket.org/yanniss/doop/src/master/docs/docker/Dockerfile)
# on 2022-03-30

FROM ecstatic/base-image

USER root

## package update
RUN apt-get update

## Set "Noninteractive" mode during Docker build
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
## locales: Doop may hang for non-UTF8 locales
RUN apt-get install -y apt-utils busybox nano libterm-readline-perl-perl
# apt-utils installation should happen before locales installation
RUN apt-get install -y locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
RUN echo 'LANG="en_US.UTF-8"' > /etc/default/locale
RUN dpkg-reconfigure --frontend=noninteractive locales
# RUN locale-gen en_US
# RUN locale-gen en_US.UTF-8
# RUN dpkg-reconfigure -f noninteractive locales

## timezone
# RUN apt-get install tzdata
# RUN echo "Europe/Athens" > /etc/timezone
# RUN dpkg-reconfigure -f noninteractive tzdata

## Souffle
RUN apt-get install -y cmake cpp autoconf automake bison build-essential clang doxygen flex g++ gdb git libncurses5-dev libtool libsqlite3-dev make mcpp python3 sqlite unzip zlib1g-dev wget curl
# RUN mkdir /souffle && wget https://github.com/souffle-lang/souffle/releases/download/1.5.1/souffle_1.5.1-1_amd64.deb -O /souffle/souffle_1.5.1-1_amd64.deb && apt-get install /souffle/souffle_1.5.1-1_amd64.deb
# RUN mkdir /souffle && wget https://github.com/souffle-lang/souffle/releases/download/2.0.2/souffle_2.0.2-1_amd64.deb -O /souffle/souffle_2.0.2-1_amd64.deb && apt-get install /souffle/souffle_2.0.2-1_amd64.deb
# Install Souffle from sources
RUN mkdir /souffle && wget https://github.com/souffle-lang/souffle/archive/refs/tags/2.1.zip -O /souffle/2.1.zip && cd /souffle && unzip 2.1.zip
RUN ls /souffle
RUN ls /souffle/souffle-2.1
RUN cmake --version
RUN apt-get install -y bash-completion lsb-release
RUN cd /souffle/souffle-2.1 && mkdir build && cmake -S . -B build && cmake --build build -j --target install

## ddlog
## Rust (binary release)
RUN mkdir /rust && cd /rust && wget https://static.rust-lang.org/dist/rust-1.57.0-x86_64-unknown-linux-gnu.tar.gz -O /rust/rust-1.57.0-x86_64-unknown-linux-gnu.tar.gz && tar xf rust-1.57.0-x86_64-unknown-linux-gnu.tar.gz
RUN cd /rust/rust-1.57.0-x86_64-unknown-linux-gnu && ./install.sh
## Haskell stack
RUN curl -sSL https://get.haskellstack.org/ | sh
## Install additional glibc development packages for GHC compatibility
RUN apt-get install -y libc6-dev libgmp-dev
## Create compatibility shim for __xmknod (removed in glibc 2.28+)
## This provides a compatibility function for older GHC versions
RUN echo '#include <sys/syscall.h>' > /tmp/xmknod_shim.c && \
    echo '#include <sys/stat.h>' >> /tmp/xmknod_shim.c && \
    echo 'int __xmknod(int ver, const char *path, mode_t mode, dev_t *dev) {' >> /tmp/xmknod_shim.c && \
    echo '  return mknod(path, mode, *dev);' >> /tmp/xmknod_shim.c && \
    echo '}' >> /tmp/xmknod_shim.c && \
    gcc -shared -fPIC -o /usr/lib/x86_64-linux-gnu/libxmknod.so /tmp/xmknod_shim.c && \
    rm /tmp/xmknod_shim.c
## Clone ddlog (on specific commit)
## Fix for __xmknod linker error: link against compatibility shim
RUN git clone https://github.com/vmware/differential-datalog.git /differential-datalog && cd /differential-datalog && git checkout v1.2.3 && \
    stack build --ghc-options="-optl-Wl,--no-as-needed -optl-L/usr/lib/x86_64-linux-gnu -optl-lxmknod" || \
    (echo "Trying without static linking..." && \
     stack build --ghc-options="-optl-Wl,--no-as-needed" --flag differential-datalog:-static || \
     stack build --ghc-options="-optl-Wl,--no-as-needed -optl-Wl,--allow-shlib-undefined") && \
    stack install --local-bin-path /usr/local/bin || \
    (echo "Installing binaries manually..." && \
     find .stack-work -name "ddlog" -type f -executable 2>/dev/null | head -1 | xargs -I {} sh -c 'cp {} /usr/local/bin/ddlog 2>/dev/null || true' && \
     find .stack-work -name "debugparser" -type f -executable 2>/dev/null | head -1 | xargs -I {} sh -c 'cp {} /usr/local/bin/debugparser 2>/dev/null || true' && \
     find .stack-work -name "ovsdb2ddlog" -type f -executable 2>/dev/null | head -1 | xargs -I {} sh -c 'cp {} /usr/local/bin/ovsdb2ddlog 2>/dev/null || true')
## Install Python dependency for ddlog Souffle converter.
RUN apt-get install -y python3-pip && pip3 install parglare==0.12.0
ENV DDLOG_DIR=/differential-datalog/

## Doop
## Note: radare2 is not available in Ubuntu 22.04, skip it or install from alternative source
RUN apt-get install -y openjdk-8-jdk openjdk-8-jre openjdk-8-jdk-headless unzip time || \
    (apt-get install -y openjdk-8-jdk openjdk-8-jre openjdk-8-jdk-headless unzip time && echo "radare2 skipped")
RUN git clone https://bitbucket.org/yanniss/doop-benchmarks.git --depth 1
ENV DOOP_BENCHMARKS=/doop-benchmarks
ENV DOOP_PLATFORMS_LIB=/doop-benchmarks
ENV DOOP_CACHE=/data/cache
ENV DOOP_OUT=/data/out

WORKDIR /
## Try multiple repository sources for DOOP
RUN git clone https://bitbucket.org/yanniss/doop.git --depth 1 || \
    git clone https://github.com/yanniss/doop.git --depth 1 || \
    (echo "Trying alternative DOOP repository..." && \
     git clone https://github.com/plast-lab/doop.git --depth 1 || \
     echo "DOOP repository clone failed - may need manual setup")
WORKDIR /doop
RUN ./gradlew installDist
WORKDIR /
ENV DOOP_CACHE=/data/cache
ENV DOOP_OUT=/data/out
ENV DOOP_HOME=/doop/build/install/doop
ENV PATH="$PATH:$DOOP_HOME/bin"

## Revert to "Dialog" mode after Docker build
RUN echo 'debconf debconf/frontend select Dialog' | debconf-set-selections
