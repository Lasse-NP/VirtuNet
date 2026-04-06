import re
import subprocess
import os
import sys
import pwd
import platform
import shutil
import tempfile
from pathlib import Path

DISTRO_FAMILIES = {
    "ubuntu": "debian",
    "debian": "debian",
    "arch": "arch",
    "manjaro": "arch",
    "cachyos": "arch",
    "fedora": "fedora",
    "rhel": "fedora",
    "centos": "fedora",
    "opensuse": "opensuse",
}

ALWAYS_INSTALL_PACKAGES = {
    "debian": ["libnetfilter-queue-dev", "build-essential", "python3.13-dev", "libxcb-cursor0"],
    "arch":   ["libnetfilter_queue", "xcb-util-cursor"],
    "fedora": ["libnetfilter_queue-devel", "gcc", "python3-devel", "xcb-util-cursor"],
    "opensuse": ["libnetfilter_queue-devel", "gcc", "python313-devel", "xcb-util-cursor"],
}

REQUIRED_COMMANDS = [
    'openvpn',      #OpenVPN
    'ovs-vsctl',    #OVSwitch
    'easyrsa',      #EasyRSA
    'mn',           #MiniNet
    'avahi-publish',    #AvahiDNS
]

PACKAGE_NAMES = {
    "debian": {
        "openvpn":  "openvpn",
        "ovs-vsctl": "openvswitch-switch",
        "easyrsa":  "easy-rsa",
        "mn":       "mininet",
        "avahi-publish":  "avahi-utils",
    },
    "arch": {
        "openvpn":  "openvpn",
        "ovs-vsctl": "openvswitch",
        "easyrsa":  "easy-rsa",
        "mn":       "mininet",
        "avahi-publish":  "avahi",
    },
    "fedora": {
        "openvpn":  "openvpn",
        "ovs-vsctl": "openvswitch",
        "easyrsa":  "easy-rsa",
        "mn":       "mininet",
        "avahi-publish":  "avahi-tools",
    },
    "opensuse": {
        "openvpn": "openvpn",
        "ovs-vsctl": "openvswitch",
        "easyrsa": "easy-rsa",
        "mn": "mininet",
        "avahi-publish":  "avahi",
    }
}

OVS_SERVICE_NAMES = [
    'openvswitch',
    'openvswitch-switch',
    'ovs-vswitchd',
]

REQUIREMENTS_FILE = Path(__file__).parent / 'requirements.txt'


def get_distro_family():
    platform_info = platform.freedesktop_os_release()

    for field in ("ID", "ID_LIKE"):
        for distro_id in platform_info.get(field, "").split():
            if distro_id in DISTRO_FAMILIES:
                return DISTRO_FAMILIES[distro_id]

    raise RuntimeError(f"Unsupported distro: {platform_info.get('PRETTY_NAME', 'unknown')}")


def start_openvswitch():
    for service in OVS_SERVICE_NAMES:
        result = subprocess.run(
            ['systemctl', 'enable', '--now', service],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            return

    raise RuntimeError('Could not start OpenVSwitch service, is it installed?')


def install_python_deps():
    if getattr(sys, 'frozen', False):
        return

    if not REQUIREMENTS_FILE.exists():
        print('*** No requirements.txt found, skipping pip install')
        return
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', str(REQUIREMENTS_FILE)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f'Failed to install Python dependencies:\n{result.stderr}')
        sys.exit(1)
    print('*** Python dependencies installed')

def check_installed(family, package):
    try:
        if family == "debian":
            result = subprocess.run(["dpkg-query", "-W", "-f=${Status}", package], capture_output=True, text=True)
            return "install ok installed" in result.stdout
        elif family == "arch":
            result = subprocess.run(["pacman", "-Q", package], capture_output=True, text=True)
            return result.returncode == 0
        elif family == "fedora":
            result = subprocess.run(["rpm", "-q", package], capture_output=True, text=True)
            return result.returncode == 0
        elif family == "opensuse":
            result = subprocess.run(["rpm", "-q", package], capture_output=True, text=True)
            return result.returncode == 0
    except FileNotFoundError:
        pass
    return False

def check_dependencies():
    family = get_distro_family()

    missing = []
    for cmd in REQUIRED_COMMANDS:
        if shutil.which(cmd) is None:
            missing.append(cmd)

    packages = [PACKAGE_NAMES[family][cmd] for cmd in missing]
    packages += [
        pkg for pkg in ALWAYS_INSTALL_PACKAGES.get(family, [])
        if not check_installed(family, pkg)
    ]

    if packages:
        try:
            if family == "debian":
                install_debian_deps(packages)
            elif family == "arch":
                install_arch_deps(packages)
            elif family == "fedora":
                install_fedora_deps(packages)
            elif family == "opensuse":
                install_opensuse_deps(packages)
        except subprocess.CalledProcessError as e:
            print(f"Failed to install packages: {e}")
            print(f"Try and fetch these yourself and rerun.")
            sys.exit(1)

    install_python_deps()

    result = subprocess.run(['ovs-vsctl', 'show'], capture_output=True)
    if result.returncode != 0:
        try:
            start_openvswitch()
        except RuntimeError as e:
            print (f"Error: {e}")
            print("Openvswitch is disabled, please enable and start it.")
            sys.exit(1)

    print('All dependencies satisfied.')


def ensure_root():
    if os.geteuid() != 0:
        print('You need root privileges to run this application.')
        sys.exit(1)


def build_from_source(package: str):
    original_user = os.environ.get("SUDO_USER")
    if not original_user:
        raise RuntimeError("Cannot determine original user for makepkg")

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chown(tmpdir, pwd.getpwnam(original_user).pw_uid, -1)
        subprocess.run(["sudo", "-u", original_user, "git", "clone", f"https://aur.archlinux.org/{package}.git"], cwd=tmpdir, check=True, text=True)
        subprocess.run(["sudo", "-u", original_user, "makepkg", "-si", "--noconfirm"], cwd=f"{tmpdir}/{package}", check=True, text=True)


def install_debian_deps(packages):
    for pack in packages:
        subprocess.run(["apt-get", "install", "-y", pack], check=True, text=True)


def install_arch_deps(packages):
    subprocess.run(["pacman", "-S", "--noconfirm", "--needed", "base-devel", "git"], check=True, text=True)
    for pack in packages:
        if pack == "mininet":
            build_from_source("mininet")
        else:
            subprocess.run(["pacman", "-S", "--noconfirm", pack], check=True, text=True)


def install_fedora_deps(packages):
    for pack in packages:
        subprocess.run(["dnf", "install", "-y", pack], check=True, text=True)


def install_opensuse_deps(packages):
    for pack in packages:
        subprocess.run(["zypper", "install", "-y", pack], check=True, text=True)