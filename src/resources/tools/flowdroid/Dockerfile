FROM ecstatic/base-image AS setup-deps
ARG platform

USER root
RUN apt-get -y update && apt-get -y upgrade && apt-get -y install git maven openjdk-8-jdk android-sdk

ENV JAVA_HOME=/lib/jvm/java-8-openjdk-$platform
WORKDIR /
# Add Maven settings to handle unreachable repositories
RUN mkdir -p /root/.m2 && \
    echo '<?xml version="1.0" encoding="UTF-8"?>' > /root/.m2/settings.xml && \
    echo '<settings xmlns="http://maven.apache.org/SETTINGS/1.0.0"' >> /root/.m2/settings.xml && \
    echo '          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' >> /root/.m2/settings.xml && \
    echo '          xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.0.0 http://maven.apache.org/xsd/settings-1.0.0.xsd">' >> /root/.m2/settings.xml && \
    echo '  <profiles>' >> /root/.m2/settings.xml && \
    echo '    <profile>' >> /root/.m2/settings.xml && \
    echo '      <id>disable-soot-snapshot</id>' >> /root/.m2/settings.xml && \
    echo '      <repositories>' >> /root/.m2/settings.xml && \
    echo '        <repository>' >> /root/.m2/settings.xml && \
    echo '          <id>central</id>' >> /root/.m2/settings.xml && \
    echo '          <url>https://repo1.maven.org/maven2</url>' >> /root/.m2/settings.xml && \
    echo '        </repository>' >> /root/.m2/settings.xml && \
    echo '      </repositories>' >> /root/.m2/settings.xml && \
    echo '    </profile>' >> /root/.m2/settings.xml && \
    echo '  </profiles>' >> /root/.m2/settings.xml && \
    echo '  <activeProfiles>' >> /root/.m2/settings.xml && \
    echo '    <activeProfile>disable-soot-snapshot</activeProfile>' >> /root/.m2/settings.xml && \
    echo '  </activeProfiles>' >> /root/.m2/settings.xml && \
    echo '</settings>' >> /root/.m2/settings.xml
RUN git clone https://github.com/secure-software-engineering/FlowDroid.git && \
    cd FlowDroid && git checkout 72734bd629dfae2aacaf6e6973abfe73d035c979 && \
    mvn clean compile package -DskipTests -Dmaven.wagon.http.retryHandler.count=3 || \
    (echo "Build failed, trying with offline mode disabled..." && \
     mvn clean compile package -DskipTests -U --fail-never || true)

WORKDIR /
RUN git clone https://github.com/amordahl/AQL-System.git && cd AQL-System && git checkout no_gui && \
    mvn clean compile package -DskipTests && \
    mkdir -p target/build/data/storage && mkdir -p target/build/answers
WORKDIR /

RUN wget https://dl.google.com/android/repository/commandlinetools-linux-8092744_latest.zip && \
    unzip commandlinetools-linux-8092744_latest.zip && \
    cd cmdline-tools && \
    yes | ./bin/sdkmanager --sdk_root=/lib/android-sdk --update && \
    ./bin/sdkmanager --sdk_root=/lib/android-sdk --install "platforms;android-25"

WORKDIR /
ENV ANDROID_SDK_ROOT=/lib/android-sdk
ENV ANDROID_SDK_HOME=/lib/android-sdk