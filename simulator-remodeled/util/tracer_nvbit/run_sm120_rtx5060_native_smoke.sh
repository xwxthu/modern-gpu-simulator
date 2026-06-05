#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

CUDA_INSTALL_PATH="${CUDA_INSTALL_PATH:-/usr/local/cuda-12.8}"
ARCH="${ARCH:-sm_120}"
SM_CONFIG_NAME="${GPGPUSIM_CONFIG:-SM120_RTX5060}"
DEVICE_NUM="${DEVICE_NUM:-0}"
WORK_DIR="${WORK_DIR:-$(mktemp -d "${TMPDIR:-/tmp}/accelsim-sm120-smoke.XXXXXX")}"
BUILD_TRACER="${BUILD_TRACER:-auto}"
BUILD_SIM="${BUILD_SIM:-auto}"
TIMEOUT_SEC="${TIMEOUT_SEC:-180}"
TRACE_NAME="${TRACE_NAME:-p3_vecadd}"

usage() {
    cat <<EOF
Usage: $(basename "$0")

Environment variables:
  CUDA_INSTALL_PATH   CUDA toolkit path (default: /usr/local/cuda-12.8)
  ARCH                CUDA/NVBit target arch (default: sm_120)
  GPGPUSIM_CONFIG    Config directory under tested-cfgs (default: SM120_RTX5060)
  DEVICE_NUM          CUDA_VISIBLE_DEVICES value (default: 0)
  WORK_DIR            Output work directory (default: mktemp under /tmp)
  BUILD_TRACER        auto|1|0, build NVBit tracer when missing (default: auto)
  BUILD_SIM           auto|1|0, build accel-sim.out when missing (default: auto)
  TIMEOUT_SEC         Timeout for traced run and simulation (default: 180)
  TRACE_NAME          Temporary app/trace name (default: p3_vecadd)

All generated CUDA source, binaries, trace files, logs, and validation summaries
are written under WORK_DIR. The script may build ignored tracer/simulator outputs
inside the repository when BUILD_TRACER/BUILD_SIM require it.
EOF
}

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

run_logged() {
    local log_file="$1"
    shift
    printf '+ %s\n' "$*" >"$log_file"
    if ! "$@" >>"$log_file" 2>&1; then
        echo "ERROR: command failed; see log: $log_file" >&2
        return 1
    fi
}

case "${1:-}" in
    -h|--help)
        usage
        exit 0
        ;;
esac

mkdir -p "$WORK_DIR"/{logs,src,bin,trace-root,validation}
WORK_DIR="$(cd "$WORK_DIR" && pwd)"
LOG_DIR="$WORK_DIR/logs"
SRC_DIR="$WORK_DIR/src"
BIN_DIR="$WORK_DIR/bin"
TRACE_ROOT="$WORK_DIR/trace-root"
TRACE_DIR="$TRACE_ROOT/traces"
VALIDATION_DIR="$WORK_DIR/validation"
mkdir -p "$TRACE_DIR"

[[ -d "$CUDA_INSTALL_PATH" ]] || fail "CUDA_INSTALL_PATH does not exist: $CUDA_INSTALL_PATH"
[[ -x "$CUDA_INSTALL_PATH/bin/nvcc" ]] || fail "nvcc not found or not executable at $CUDA_INSTALL_PATH/bin/nvcc"
export CUDA_INSTALL_PATH
export PATH="$CUDA_INSTALL_PATH/bin:$PATH"
export LD_LIBRARY_PATH="$CUDA_INSTALL_PATH/lib64:${LD_LIBRARY_PATH:-}"

command -v make >/dev/null 2>&1 || fail "make is required"
command -v timeout >/dev/null 2>&1 || fail "timeout is required"

TRACER_SO="$SCRIPT_DIR/tracer_tool/tracer_tool.so"
TRACE_PRINTER="$SCRIPT_DIR/tracer_tool/trace_printer"
if [[ "$BUILD_TRACER" == "1" || ( "$BUILD_TRACER" == "auto" && ( ! -f "$TRACER_SO" || ! -x "$TRACE_PRINTER" ) ) ]]; then
    run_logged "$LOG_DIR/build-tracer.log" make -C "$SCRIPT_DIR" ARCH="$ARCH"
elif [[ ! -f "$TRACER_SO" || ! -x "$TRACE_PRINTER" ]]; then
    fail "NVBit tracer outputs are missing; rerun with BUILD_TRACER=1 or BUILD_TRACER=auto"
fi

ACCEL_SIM="$SIM_ROOT/gpu-simulator/bin/release/accel-sim.out"
if [[ "$BUILD_SIM" == "1" || ( "$BUILD_SIM" == "auto" && ! -x "$ACCEL_SIM" ) ]]; then
    (
        cd "$SIM_ROOT"
        set +u
        # shellcheck source=/dev/null
        source "$SIM_ROOT/gpu-simulator/setup_environment_no_git.sh" release
        set -u
        run_logged "$LOG_DIR/build-simulator.log" make -C "$SIM_ROOT/gpu-simulator" -j"$(nproc)"
    )
elif [[ ! -x "$ACCEL_SIM" ]]; then
    fail "Simulator binary is missing; rerun with BUILD_SIM=1 or BUILD_SIM=auto"
fi

GPGPUSIM_CONFIG_FILE="$SIM_ROOT/gpu-simulator/gpgpu-sim/configs/tested-cfgs/$SM_CONFIG_NAME/gpgpusim.config"
TRACE_CONFIG_FILE="$SIM_ROOT/gpu-simulator/configs/tested-cfgs/$SM_CONFIG_NAME/trace.config"
[[ -f "$GPGPUSIM_CONFIG_FILE" ]] || fail "GPGPU-Sim config not found: $GPGPUSIM_CONFIG_FILE"
[[ -f "$TRACE_CONFIG_FILE" ]] || fail "Trace config not found: $TRACE_CONFIG_FILE"

APP_SRC="$SRC_DIR/$TRACE_NAME.cu"
APP_BIN="$BIN_DIR/$TRACE_NAME"
cat >"$APP_SRC" <<'CU'
#include <cstdio>
#include <cstdlib>
#include <cuda_runtime.h>

__global__ void vecadd_kernel(const float *a, const float *b, float *c, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

static void check(cudaError_t err, const char *what) {
    if (err != cudaSuccess) {
        std::fprintf(stderr, "%s: %s\n", what, cudaGetErrorString(err));
        std::exit(1);
    }
}

int main() {
    const int n = 64;
    float h_a[n], h_b[n], h_c[n];
    for (int i = 0; i < n; ++i) {
        h_a[i] = static_cast<float>(i);
        h_b[i] = static_cast<float>(2 * i);
        h_c[i] = 0.0f;
    }

    float *d_a = nullptr, *d_b = nullptr, *d_c = nullptr;
    check(cudaMalloc(&d_a, n * sizeof(float)), "cudaMalloc d_a");
    check(cudaMalloc(&d_b, n * sizeof(float)), "cudaMalloc d_b");
    check(cudaMalloc(&d_c, n * sizeof(float)), "cudaMalloc d_c");
    check(cudaMemcpy(d_a, h_a, n * sizeof(float), cudaMemcpyHostToDevice), "copy a");
    check(cudaMemcpy(d_b, h_b, n * sizeof(float), cudaMemcpyHostToDevice), "copy b");

    vecadd_kernel<<<1, 64>>>(d_a, d_b, d_c, n);
    check(cudaGetLastError(), "kernel launch");
    check(cudaDeviceSynchronize(), "kernel sync");
    check(cudaMemcpy(h_c, d_c, n * sizeof(float), cudaMemcpyDeviceToHost), "copy c");

    for (int i = 0; i < n; ++i) {
        float expected = h_a[i] + h_b[i];
        if (h_c[i] != expected) {
            std::fprintf(stderr, "mismatch at %d: got %f expected %f\n", i, h_c[i], expected);
            return 2;
        }
    }

    check(cudaFree(d_a), "free a");
    check(cudaFree(d_b), "free b");
    check(cudaFree(d_c), "free c");
    std::puts("p3_vecadd_ok");
    return 0;
}
CU

run_logged "$LOG_DIR/compile-$TRACE_NAME.log" "$CUDA_INSTALL_PATH/bin/nvcc" -arch="$ARCH" "$APP_SRC" -o "$APP_BIN"
(
    export CUDA_VISIBLE_DEVICES="$DEVICE_NUM"
    run_logged "$LOG_DIR/native-$TRACE_NAME.log" "$APP_BIN"
)

(
    cd "$TRACE_ROOT"
    export CUDA_VISIBLE_DEVICES="$DEVICE_NUM"
    export CUDA_VERSION
    CUDA_VERSION="$("$CUDA_INSTALL_PATH/bin/nvcc" --version | grep release | sed -re 's/.*release ([0-9]+\.[0-9]+).*/\1/')"
    export USER_DEFINED_FOLDERS=1
    export TRACES_FOLDER="$TRACE_DIR"
    export CUDA_INJECTION64_PATH="$TRACER_SO"
    export LD_PRELOAD="$TRACER_SO"
    run_logged "$LOG_DIR/trace-$TRACE_NAME.log" timeout "$TIMEOUT_SEC" "$APP_BIN"
)

[[ -f "$TRACE_DIR/dynamic_trace.pb" ]] || fail "Trace generation did not create $TRACE_DIR/dynamic_trace.pb"
[[ -f "$TRACE_DIR/stats.csv" ]] || fail "Trace generation did not create $TRACE_DIR/stats.csv"
[[ -f "$TRACE_DIR/extra_info/enhanced_execution_info.json" ]] || fail "Trace generation did not create enhanced execution metadata"

printf -- "-2\n" | "$TRACE_PRINTER" "$TRACE_DIR" >"$VALIDATION_DIR/trace-printer.txt" 2>&1 || fail "trace_printer could not parse $TRACE_DIR"
grep -q "Binary Version.*: 120" "$VALIDATION_DIR/trace-printer.txt" || fail "Trace metadata does not report Binary Version 120"
grep -q "NVBIT Version.*: 1.7.5" "$VALIDATION_DIR/trace-printer.txt" || fail "Trace metadata does not report NVBIT Version 1.7.5"
grep -q "Number of Devices.*: 1" "$VALIDATION_DIR/trace-printer.txt" || fail "Trace metadata does not report one device"
grep -q "vecadd_kernel" "$TRACE_DIR/stats.csv" || fail "stats.csv does not include vecadd_kernel"
grep -q "total_insts" "$TRACE_DIR/stats.csv" || fail "stats.csv header is missing total_insts"
grep -q "total_reported_insts" "$TRACE_DIR/stats.csv" || fail "stats.csv header is missing total_reported_insts"
awk -F, '/vecadd_kernel/ {
    gsub(/ /, "", $(NF-1));
    gsub(/ /, "", $NF);
    if ($(NF-1) + 0 > 0 && $NF + 0 > 0) {
        found = 1
    }
}
END { exit found ? 0 : 1 }' "$TRACE_DIR/stats.csv" || fail "stats.csv does not report positive instruction counters for vecadd_kernel"

(
    cd "$SIM_ROOT"
    set +u
    # shellcheck source=/dev/null
    source "$SIM_ROOT/gpu-simulator/setup_environment_no_git.sh" release
    set -u
    run_logged "$LOG_DIR/sim-$TRACE_NAME-$SM_CONFIG_NAME.log" timeout "$TIMEOUT_SEC" "$ACCEL_SIM" \
        -trace "$TRACE_DIR/dynamic_trace.pb" \
        -config "$GPGPUSIM_CONFIG_FILE" \
        -config "$TRACE_CONFIG_FILE"
)

SIM_LOG="$LOG_DIR/sim-$TRACE_NAME-$SM_CONFIG_NAME.log"
grep -q "GPGPU-Sim: \\*\\*\\* exit detected \\*\\*\\*" "$SIM_LOG" || fail "Simulator log does not contain exit detected marker"
grep -Eq -- "-gpgpu_n_clusters[[:space:]]+30" "$SIM_LOG" || fail "Simulator log does not show RTX5060 cluster count"
grep -Eq -- "-gpgpu_n_mem[[:space:]]+8" "$SIM_LOG" || fail "Simulator log does not show RTX5060 memory partition count"
grep -Eq "gpu_tot_sim_insn = [1-9][0-9]*" "$SIM_LOG" || fail "Simulator log does not contain positive gpu_tot_sim_insn"
grep -Eq "gpu_tot_issued_cta = [1-9][0-9]*" "$SIM_LOG" || fail "Simulator log does not contain positive gpu_tot_issued_cta"

cat >"$VALIDATION_DIR/summary.txt" <<EOF
status=PASS
work_dir=$WORK_DIR
cuda_install_path=$CUDA_INSTALL_PATH
arch=$ARCH
gpgpusim_config=$SM_CONFIG_NAME
device_num=$DEVICE_NUM
trace_dir=$TRACE_DIR
dynamic_trace=$TRACE_DIR/dynamic_trace.pb
stats_csv=$TRACE_DIR/stats.csv
trace_metadata=$VALIDATION_DIR/trace-printer.txt
simulation_log=$SIM_LOG
EOF

cat "$VALIDATION_DIR/summary.txt"
