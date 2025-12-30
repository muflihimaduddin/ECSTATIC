#!/bin/bash

# Clone repository
apt-get update -y
apt-get install -y parallel ant javacc unzip
CUR=$(pwd)
mkdir -p /benchmarks
cd /benchmarks
if [ ! -d "Dacapo-2006" ]; then
git clone https://github.com/amordahl/Dacapo-2006.git
fi
cd Dacapo-2006/benchmarks/build_scripts
# Ensure ant is in PATH
export PATH="/usr/bin:$PATH"
# Run build scripts
find . -type f -name '*.sh' -exec bash {} \;
cd $CUR