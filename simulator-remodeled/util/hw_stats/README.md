# Instructions on generating the hardware data for correlation

## SM120 lightweight device-info collection

S3 adds `collect_sm120_device_info.py` for official-tool collection before any
benchmark or simulator work. It runs short `nvidia-smi`, `nvcc`, `ncu`, and
`nsys` queries and stores the outputs locally under `util/hw_stats/device_info/`
(ignored by git).

Examples:

```bash
# Local dry run, useful for checking output layout.
python3 collect_sm120_device_info.py --dry-run

# Collect from the RTX 5060 host without placing this workspace there.
python3 collect_sm120_device_info.py --remote dsp5060 --device 0

# Optional Nsight Compute metric discovery for later S4/S5 metric mapping.
python3 collect_sm120_device_info.py --remote dsp5060 --device 0 --include-metric-discovery
```

Each run creates a timestamped local directory with `manifest.json` plus
`*.stdout.txt` and `*.stderr.txt` files. Nonzero command statuses are recorded in
the manifest instead of being hidden; use `--strict` only when a caller wants
any missing tool to fail the script.

The script is intentionally limited to official tool and version queries. It
does not run full simulations, application benchmarks, or calibration
microbenchmarks.

## Legacy correlation hardware data

* Make sure CUDA\_INSTALL\_PATH is set and bin/lib directories are in PATH and LD\_LIBRARY\_PATH
* Build the benchmarks
```bash
# Get the applications, their data files and build them:··
git clone https://github.com/accel-sim/gpu-app-collection··
source ./gpu-app-collection/src/setup_environment··
make -j -C ./gpu-app-collection/src rodinia_2.0-ft··
make -C ./gpu-app-collection/src data··
```

* Run the hardware correl

```bash
# In this folder there are shell scripts that kick off the hardware exectuion, bundle the resutls then publish them online.
# Obviously your commands will not be exact. The most imporant part of this file is the ./run_hw.py command. It takes the exact same benchmark
# definitions as the run_simulations.py command in the util/job_launching folder - ensuring there is a 1:1 relationship between apps run
# in simulation and apps run in hardware.
# To run a set of apps in hardware use the -B command, just like in run_simulations.py. An example:
./run_hw.py -D 0 -B rodinia_2.0-ft -R 10 -c
# ./run_hw.py --help gives a full explanation, but the important switches in this statement are:
# -D <device number returned by the SDK's deviceQuerry (Note: this is often different from nvidia-smi's device number)>
# -B <benchmark list - same format as run_simulations.py>
# -R <number of times to run the cycle tests (not every hardware run takes the same time - error bars will get created on the x-axis of correlation)>
# -c passing this parameter only runs the cycle correlation data. without this swtich both cycle timing AND all the statistics profiling will be done
#   the full stats profiling takes MUCH longer.
```
