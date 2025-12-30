FROM ubuntu:20.04 as wala-install

USER root
## timezone
RUN apt-get update && \
    apt-get install -yq tzdata && \
    ln -fs /usr/share/zoneinfo/America/Chicago /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata

## package update
RUN apt-get update && apt-get install -y git openjdk-11-jdk maven

WORKDIR /
RUN git clone https://github.com/amordahl/WALAInterface --depth 1
WORKDIR /WALAInterface
RUN mvn compile package

FROM ecstatic/base-image

RUN apt-get update && \
    apt-get install -y wget gnupg && \
    mkdir -p /etc/apt/keyrings && \
    wget -O - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | tee /etc/apt/sources.list.d/adoptium.list && \
    apt-get update && \
    apt-get install -y temurin-11-jdk && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME to the Temurin installation
ENV JAVA_HOME=/usr/lib/jvm/temurin-11-jdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Create symlink for java-11-openjdk-amd64/jmods that WALA expects
# WALA looks for /usr/lib/jvm/java-11-openjdk-amd64/jmods
# If java-11-openjdk-amd64 exists but doesn't have jmods, create a symlink
RUN if [ -d /usr/lib/jvm/java-11-openjdk-amd64 ] && [ ! -d /usr/lib/jvm/java-11-openjdk-amd64/jmods ]; then \
        if [ -L /usr/lib/jvm/java-11-openjdk-amd64 ]; then \
            rm /usr/lib/jvm/java-11-openjdk-amd64 && \
            ln -s /usr/lib/jvm/temurin-11-jdk-amd64 /usr/lib/jvm/java-11-openjdk-amd64; \
        else \
            ln -s /usr/lib/jvm/temurin-11-jdk-amd64/jmods /usr/lib/jvm/java-11-openjdk-amd64/jmods; \
        fi; \
    elif [ ! -e /usr/lib/jvm/java-11-openjdk-amd64 ]; then \
        ln -s /usr/lib/jvm/temurin-11-jdk-amd64 /usr/lib/jvm/java-11-openjdk-amd64; \
    fi

COPY --from=wala-install /WALAInterface /WALAInterface

# Fix wala.properties to use the correct Java path
RUN sed -i 's|java_runtime_dir=.*|java_runtime_dir=/usr/lib/jvm/temurin-11-jdk-amd64|g' /WALAInterface/src/main/resources/wala.properties /WALAInterface/target/classes/wala.properties 2>/dev/null || true