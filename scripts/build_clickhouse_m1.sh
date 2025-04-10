#!/bin/bash

set -e

echo "==============================================="
echo "   🚀 ClickHouse Native Build for Apple Silicon"
echo "==============================================="
echo ""
echo "⚠️  WARNING: This build process can take **30-90 minutes** depending on hardware."
echo "Please be patient. Do NOT interrupt."
echo ""

echo "Estimated Timeline:"
echo ""
echo "🟢 Step 1: Dependencies (2-5 min)"
echo "🟡 Step 2: Clone/Update Repo (1-2 min)"
echo "🟡 Step 3: Configure Build (1-2 min)"
echo "🔴 Step 4: Compile ClickHouse (30-90 min)"
echo ""
echo "Progress:"
echo "[🟢] Dependencies --> [🟡] Clone --> [🟡] Configure --> [🔴] Build --> [✅] Done"
echo ""

echo "==============================================="
echo "Step 1: Installing dependencies via Homebrew..."
echo "==============================================="
brew update
brew install cmake ninja llvm openssl zlib bison flex

echo ""
echo "==============================================="
echo "Step 2: Cloning or updating ClickHouse repository..."
echo "==============================================="
if [ ! -d "ClickHouse" ]; then
  git clone --recursive https://github.com/ClickHouse/ClickHouse.git
else
  cd ClickHouse
  git pull
  git submodule update --init --recursive
  cd ..
fi

cd ClickHouse

echo ""
echo "==============================================="
echo "Step 3: Configuring CMake for Apple Silicon ARM64 optimized minimal build..."
echo "==============================================="
mkdir -p build
cd build

cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_CXX_COMPILER=clang++ \
  -DENABLE_TESTS=OFF \
  -DENABLE_BENCHMARKS=OFF \
  -DENABLE_KAFKA=OFF \
  -DENABLE_MYSQL=OFF \
  -DENABLE_HDFS=OFF \
  -DENABLE_ODBC=OFF \
  -DENABLE_CASSANDRA=OFF \
  -DENABLE_RDKAFKA=OFF \
  -DENABLE_JEMALLOC=ON \
  -DENABLE_PROTOBUF=OFF \
  -DENABLE_GRPC=OFF \
  -DENABLE_HYPERSCAN=OFF \
  -DENABLE_EMBEDDED_COMPILER=OFF \
  -DENABLE_TCMALLOC=OFF \
  -DENABLE_CLICKHOUSE_KEEPER=OFF \
  -DENABLE_CLICKHOUSE_SERVER=ON \
  -DENABLE_CLICKHOUSE_CLIENT=ON \
  -DENABLE_CLICKHOUSE_LOCAL=ON \
  -DENABLE_CLICKHOUSE_BENCHMARK=OFF \
  -DENABLE_CLICKHOUSE_TEST=OFF \
  -DENABLE_CLICKHOUSE_GIT_IMPORT=OFF \
  -DENABLE_CLICKHOUSE_ODBC_BRIDGE=OFF \
  -DENABLE_CLICKHOUSE_LIBRARY_BRIDGE=OFF \
  -DENABLE_CLICKHOUSE_COMBINATOR=OFF \
  -DENABLE_CLICKHOUSE_COPIER=OFF \
  -DENABLE_CLICKHOUSE_OBSERVER=OFF \
  -DENABLE_CLICKHOUSE_DISK_CACHE=OFF \
  -DENABLE_CLICKHOUSE_DISK_S3=OFF \
  -DENABLE_CLICKHOUSE_DISK_HDFS=OFF \
  -DENABLE_CLICKHOUSE_DISK_WEB=OFF \
  -DENABLE_CLICKHOUSE_DISK_LOCAL=ON \
  -DENABLE_CLICKHOUSE_DISK_ENCRYPTED=OFF \
  -DENABLE_CLICKHOUSE_DISK_CACHE=OFF \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DCMAKE_C_FLAGS="-mcpu=apple-m1" \
  -DCMAKE_CXX_FLAGS="-mcpu=apple-m1"

echo ""
echo "==============================================="
echo "Step 4: Building ClickHouse (this will take a long time)..."
echo "==============================================="
cmake --build . --target clickhouse -- -j$(sysctl -n hw.ncpu)

echo ""
echo "==============================================="
echo "✅ ClickHouse build complete!"
echo "Binaries located in ClickHouse/build/programs"
echo "==============================================="