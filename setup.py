import subprocess
import os
import sys
import pwd
import platform
import shutil
import tempfile

REQUIRED_COMMANDS = [
    'openvpn',      #OpenVPN
    'ovs-vsctl',    #OVSwitch
    'easyrsa',      #EasyRSA
    'mn'            #MiniNet
]

PACKAGE_NAMES = {
    "debian": {
        "openvpn":  "openvpn",
        "ovs-vsctl": "openvswitch-switch",
        "easyrsa":  "easy-rsa",
        "mn":       "mininet",
    },
    "arch": {
        "openvpn":  "openvpn",
        "ovs-vsctl": "openvswitch",
        "easyrsa":  "easy-rsa",
        "mn":       "mininet",
    },
    "fedora": {
        "openvpn":  "openvpn",
        "ovs-vsctl": "openvswitch",
        "easyrsa":  "easy-rsa",
        "mn":       "mininet",
    },
    "opensuse": {
        "openvpn": "openvpn",
        "ovs-vsctl": "openvswitch",
        "easyrsa": "easy-rsa",
        "mn": "mininet",
    }
}

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

OVS_SERVICE_NAMES = [
    'openvswitch',
    'openvswitch-switch',
    'ovs-vswitchd',
]

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

def check_dependencies():
    family = get_distro_family()

    missing = []
    for cmd in REQUIRED_COMMANDS:
        if shutil.which(cmd) is None:
            missing.append(cmd)

    packages = [PACKAGE_NAMES[family][cmd] for cmd in missing]

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
    subprocess.run(["pacman", "-S", "--noconfirm", "base-devel", "git"], check=True, text=True)
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