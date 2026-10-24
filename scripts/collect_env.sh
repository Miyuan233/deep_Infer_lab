#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
output_dir="${1:-${project_root}/results/m0/${timestamp}-environment}"
conda_bin="${CONDA_EXE:-${HOME}/anaconda3/bin/conda}"

if [[ -e "${output_dir}" ]]; then
  echo "Refusing to overwrite existing output: ${output_dir}" >&2
  exit 2
fi

mkdir -p "${output_dir}"

{
  printf 'timestamp_utc=%s\n' "${timestamp}"
  printf 'hostname=%s\n' "$(hostname)"
  printf 'user=%s\n' "$(id -un)"
  printf 'project_root=%s\n' "${project_root}"
  printf 'git_commit=%s\n' "$(git -C "${project_root}" rev-parse HEAD 2>/dev/null || printf unknown)"
  printf 'git_dirty=%s\n' "$(test -n "$(git -C "${project_root}" status --porcelain 2>/dev/null)" && printf true || printf false)"
} > "${output_dir}/manifest.txt"

cat /etc/os-release > "${output_dir}/os-release.txt"
uname -a > "${output_dir}/uname.txt"
lscpu > "${output_dir}/lscpu.txt"
free -h > "${output_dir}/memory.txt"
df -h "${project_root}" > "${output_dir}/disk.txt"
nvidia-smi > "${output_dir}/nvidia-smi.txt"
nvidia-smi -L > "${output_dir}/nvidia-smi-list.txt"
nvidia-smi topo -m > "${output_dir}/nvidia-topology.txt"
nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,memory.total,memory.used,utilization.gpu,temperature.gpu,driver_version,pstate --format=csv > "${output_dir}/nvidia-gpus.csv"
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_memory --format=csv > "${output_dir}/nvidia-processes.csv" || true

"${conda_bin}" info --envs > "${output_dir}/conda-envs.txt"
"${conda_bin}" list -n infer-h200 > "${output_dir}/conda-list-infer-h200.txt"
"${conda_bin}" run -n infer-h200 python -VV > "${output_dir}/python-version.txt"
"${conda_bin}" run -n infer-h200 python -m pip freeze --all > "${output_dir}/pip-freeze-infer-h200.txt"
"${conda_bin}" run -n infer-h200 python -m pip check > "${output_dir}/pip-check.txt"

for tool in nvcc nsys ncu cmake ninja gcc g++ git; do
  {
    printf '%s=' "${tool}"
    command -v "${tool}" || printf 'NOT_FOUND\n'
  } >> "${output_dir}/tool-paths.txt"
done

find "${CONDA_PREFIX:-${HOME}/anaconda3/envs/infer-h200}" -type f \
  \( -name nvcc -o -name ptxas -o -name nsys -o -name ncu \) \
  -print > "${output_dir}/bundled-cuda-tools.txt" 2>/dev/null || true

echo "Environment snapshot written to ${output_dir}"
