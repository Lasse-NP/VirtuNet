import re
import subprocess
import os
import sys
import pwd
import platform
import shutil
import tempfile
from pathlib import Path

# Maps specific distro IDs (from /etc/os-release) to a canonical family name used for package management.
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

# System packages that must always be installed regardless of which commands are already present.
# Includes native libraries required by Python extensions (e.g. netfilter-queue, xcb) that pip cannot provide.
ALWAYS_INSTALL_PACKAGES = {
    "debian": ["libnetfilter-queue-dev", "build-essential", "python3.13-dev", "libxcb-cursor0", "openvswitch-testcontroller"],
    "arch":   ["libnetfilter_queue", "xcb-util-cursor", "net-tools", "iperf"],
    "fedora": ["libnetfilter_queue-devel", "gcc", "python3-devel", "xcb-util-cursor"],
    "opensuse": ["libnetfilter_queue-devel", "gcc", "python313-devel", "xcb-util-cursor"],
}

# CLI commands that must be resolvable on PATH for the application to function.
# Each entry is checked with shutil.which; missing ones are mapped to packages via PACKAGE_NAMES.
REQUIRED_COMMANDS = [
    'openvpn',          # OpenVPN: creates and manages the VPN tunnel clients connect through.
    'ovs-vsctl',        # Open vSwitch: virtual switch used by Mininet to connect virtual hosts.
    'easyrsa',          # EasyRSA: generates the PKI certificates needed by OpenVPN.
    'mn',               # Mininet: creates and manages the virtual network topology.
    'avahi-publish',    # Avahi: broadcasts mDNS records so virtual hosts resolve by hostname.
]

# Maps each required command to its installable package name on each distro family.
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

# Possible systemd service names for Open vSwitch across different distros.
# Tried in order; the first one that starts successfully wins.
OVS_SERVICE_NAMES = [
    'openvswitch',
    'openvswitch-switch',
    'ovs-vswitchd',
]

# Path to the pip requirements file, resolved relative to this script so it works from any working directory.
REQUIREMENTS_FILE = Path(__file__).parent / 'requirements.txt'


def get_distro_family():
    # Read /etc/os-release fields into a dict using the stdlib helper.
    platform_info = platform.freedesktop_os_release()

    # Check both ID (e.g. "manjaro") and ID_LIKE (e.g. "arch") so derivatives map correctly.
    for field in ("ID", "ID_LIKE"):
        for distro_id in platform_info.get(field, "").split():
            if distro_id in DISTRO_FAMILIES:
                return DISTRO_FAMILIES[distro_id]

    # No recognised distro found; raise with the human-readable name from PRETTY_NAME for clear error output.
    raise RuntimeError(f"Unsupported distro: {platform_info.get('PRETTY_NAME', 'unknown')}")


def start_openvswitch():
    # Try each known service name in turn; distros package OVS under different unit names.
    for service in OVS_SERVICE_NAMES:
        result = subprocess.run(
            ['systemctl', 'enable', '--now', service],
            capture_output=True, text=True
        )
        # A zero return code means the service started; no need to try further names.
        if result.returncode == 0:
            return

    # None of the known service names worked; surface a clear error so the user knows what to fix.
    raise RuntimeError('Could not start OpenVSwitch service, is it installed?')


def install_python_deps():
    # Skip pip install entirely when running as a compiled executable; deps are bundled.
    if getattr(sys, 'frozen', False):
        return

    if not REQUIREMENTS_FILE.exists():
        print('*** No requirements.txt found, skipping pip install')
        return
    
    # Install all python dependencies.
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', str(REQUIREMENTS_FILE)],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f'Failed to install Python dependencies:\n{result.stderr}')
        sys.exit(1)
    print('*** Python dependencies installed')

def check_installed(family, package):
    # Query the native package manager to check if a package is already installed.
    # Returns False on FileNotFoundError so an absent package manager is treated as not-installed.
    try:
        if family == "debian":
            # dpkg-query exits 0 and prints "install ok installed" for installed packages.
            result = subprocess.run(["dpkg-query", "-W", "-f=${Status}", package], capture_output=True, text=True)
            return "install ok installed" in result.stdout
        elif family == "arch":
            # pacman -Q exits 0 if the package is installed, non-zero otherwise.
            result = subprocess.run(["pacman", "-Q", package], capture_output=True, text=True)
            return result.returncode == 0
        elif family == "fedora":
            # rpm -q exits 0 if the package is installed, non-zero otherwise.
            result = subprocess.run(["rpm", "-q", package], capture_output=True, text=True)
            return result.returncode == 0
        elif family == "opensuse":
            # OpenSUSE also uses rpm as its low-level package database.
            result = subprocess.run(["rpm", "-q", package], capture_output=True, text=True)
            return result.returncode == 0
    except FileNotFoundError:
        pass
    return False

def check_dependencies():
    family = get_distro_family()

    # Collect every required command that cannot be found on PATH.
    missing = []
    for cmd in REQUIRED_COMMANDS:
        if shutil.which(cmd) is None:
            missing.append(cmd)

    # Map each missing command to its distro-specific package name.
    packages = [PACKAGE_NAMES[family][cmd] for cmd in missing]

    # Append always-required native library packages that are not yet installed.
    packages += [
        pkg for pkg in ALWAYS_INSTALL_PACKAGES.get(family, [])
        if not check_installed(family, pkg)
    ]

    # Installs all the found missing/always-install packages.
    if packages:
        try:
            match family:
                case "debian":
                    install_debian_deps(packages)
                case "arch":
                    install_arch_deps(packages)
                case "fedora":
                    install_fedora_deps(packages)
                case "opensuse":
                    install_opensuse_deps(packages)
        except subprocess.CalledProcessError as e:
            # A package manager failure is unrecoverable here; tell the user what failed and exit.
            print(f"Failed to install packages: {e}")
            print("Try and fetch these yourself and rerun.")
            sys.exit(1)

    # Install Python-level dependencies after system packages, since some wheels need the native libs above.
    install_python_deps()

    # Verify OVS is actually running, not just installed; a stopped daemon causes Mininet to fail silently.
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
    # Mininet, iptables, and OpenVPN all require root; exit immediately with a clear message if not root.
    if os.geteuid() != 0:
        print('You need root privileges to run this application.')
        sys.exit(1)


def build_from_source(package: str):
    # Determine the original non-root user so makepkg can run without root, which it refuses to do.
    original_user = subprocess.check_output(['logname'], text=True).strip()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Give the temp directory to the original user so git and makepkg can write to it.
        os.chown(tmpdir, pwd.getpwnam(original_user).pw_uid, -1)
        # Clone the AUR package repository as the non-root user.
        subprocess.run(["sudo", "-u", original_user, "git", "clone", f"https://aur.archlinux.org/{package}.git"], cwd=tmpdir, check=True, text=True)
        # Build and install the package; --skippgpcheck avoids GPG key issues in headless environments.
        subprocess.run(["sudo", "-u", original_user, "makepkg", "-si", "--noconfirm", "--skippgpcheck"], cwd=f"{tmpdir}/{package}", check=True, text=True)


def install_debian_deps(packages):
    # Install each package individually so a single failure does not silently skip the rest.
    for pack in packages:
        subprocess.run(["apt-get", "install", "-y", pack], check=True, text=True)

    # Create symlinks for tools that are installed but not placed on PATH by the package.
    symlinks = [
        # easy-rsa installs its script to /usr/share but does not add a PATH entry on Debian.
        ('/usr/share/easy-rsa/easyrsa', '/usr/local/bin/easyrsa'),
        # The OVS test controller binary has a versioned name; alias it as 'controller' for Mininet.
        ('/usr/bin/ovs-testcontroller', '/usr/local/bin/controller')
    ]

    for src, dst in symlinks:
        # Only create the symlink if the source exists and the destination is not already on PATH.
        if os.path.exists(src) and not shutil.which(os.path.basename(dst)):
            os.symlink(src, dst)


def install_arch_deps(packages):
    # Ensure base-devel and git are present before attempting AUR builds.
    subprocess.run(["pacman", "-S", "--noconfirm", "--needed", "base-devel", "git"], check=True, text=True)
    for pack in packages:
        if pack == "mininet":
            # Mininet is not in the official Arch repos; install its AUR dependency then build it from AUR.
            if not check_installed("arch", "libcgroup"):
                build_from_source("libcgroup")
            build_from_source("mininet")
        else:
            subprocess.run(["pacman", "-S", "--noconfirm", pack], check=True, text=True)

    # easy-rsa on Arch installs to /usr/share without a PATH symlink, same as Debian.
    if shutil.which('easyrsa') is None:
        easyrsa_src = '/usr/share/easy-rsa/easyrsa'
        if os.path.exists(easyrsa_src):
            os.symlink(easyrsa_src, '/usr/local/bin/easyrsa')


def install_fedora_deps(packages):
    # Install each package individually so failures are visible per-package.
    for pack in packages:
        subprocess.run(["dnf", "install", "-y", pack], check=True, text=True)


def install_opensuse_deps(packages):
    # Install each package individually so failures are visible per-package.
    for pack in packages:
        subprocess.run(["zypper", "install", "-y", pack], check=True, text=True)