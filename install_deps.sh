#!/usr/bin/env bash
# Dependencies of the TidyBot++ code (this repository) on Ubuntu 22.04.
# Run once from the repository root, inside the activated virtual
# environment (README.md, "at_home 설치"):
#   source ~/at_home_tidybot/bin/activate && ./install_deps.sh
# --skip-system installs only the python packages (no apt).
set -euo pipefail

skip_system=false
[[ "${1:-}" == "--skip-system" ]] && skip_system=true

# Python packages go into the virtual environment, never the system/user
# site. base_ros_node.py needs the ROS python packages (rclpy, ...), so the
# venv must be created with --system-site-packages.
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo "Activate the virtual environment first:" >&2
    echo "  python3 -m venv --system-site-packages ~/at_home_tidybot && source ~/at_home_tidybot/bin/activate" >&2
    exit 1
fi
if ! grep -q "include-system-site-packages = true" "$VIRTUAL_ENV/pyvenv.cfg"; then
    echo "$VIRTUAL_ENV was created without --system-site-packages; ROS python" >&2
    echo "packages are not visible in it. Recreate it with that option." >&2
    exit 1
fi
# conda's python and site settings break the system ROS python packages.
if [[ -n "${CONDA_PREFIX:-}" ]]; then
    echo "Deactivate conda first (conda deactivate), then run again." >&2
    exit 1
fi

if ! $skip_system; then
    echo "== apt packages"
    # Same list as the Dockerfile: CAN tools, joystick, USB and GL/X runtime.
    sudo apt-get update
    sudo apt-get install -y \
        build-essential git python3-venv iproute2 can-utils joystick \
        libusb-1.0-0 libgl1 libglib2.0-0 libx11-6 libxext6 libxrender1 libsm6
fi

# --system-site-packages also exposes the user site (~/.local), whose numpy
# would shadow the pinned one; the venv ignores it.
if ! grep -q "PYTHONNOUSERSITE" "$VIRTUAL_ENV/bin/activate"; then
    printf '\n# at_home_tidybot: ignore ~/.local packages\nexport PYTHONNOUSERSITE=1\n' \
        >> "$VIRTUAL_ENV/bin/activate"
fi
export PYTHONNOUSERSITE=1

echo "== python packages ($VIRTUAL_ENV)"
# requirements-env.txt is the frozen package set of the working tidybot2
# environment. pip / setuptools / wheel are left to the venv: setuptools 84
# breaks the system colcon (setuptools < 80).
requirements="$(mktemp)"
grep -vE '^(pip|setuptools|wheel)==' requirements-env.txt > "$requirements"
python -m pip install -r "$requirements"
rm -f "$requirements"

python -c "import numpy, mujoco, pinocchio, phoenix6, pygame, cv2; print('numpy', numpy.__version__, '|', numpy.__file__)"
echo "Done. See README.md (at_home 설치) for running the base."
