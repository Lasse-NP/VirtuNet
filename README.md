<div align="center">

  <img src="GUI/Assets/VirtuNetIcon.png" alt="logo" width="400" height="auto" />
  <h1>VirtuNet Instructor </h1>
  
  <p>
    A Virtual Network Builder with GUI and CLI
  </p>

   <h4>
      <a href="https://github.com/Lasse-NP/VirtuNet">View Demo</a>
    <span> · </span>
      <a href="https://github.com/Lasse-NP/VirtuNet/wiki">Documentation</a>
    <span> · </span>
      <a href="https://github.com/Lasse-NP/VirtuNet/issues">Report Bug</a>
   </h4>
</div>


# Table of Contents

- [About the Project](#about-the-project)
  * [Screenshots](#screenshots)
- [Getting Started](#getting-started)
  * [Supported Distros](#supported-distros)
  * [Installation](#installation)
- [Usage](#usage)
- [Dependencies](#dependencies)

## About the Project
VirtuNet is a complex virtual network builder that allows you to create virtual training environments specifically for NMAP. 
This program is made specifically with NMAP in mind, which means that other network scanning tools haven't been tested properly.

**Keep in mind that you will also need clients to connect to the virtual network through the [VirtuNet-Client](https://github.com/Lasse-NP/VirtuNet-Client) sister project**

### Screenshots
<img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/dbcaa2db-8afa-4b87-baae-081fbf020661" />
<img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/f9ade818-a1e7-4b5b-83a1-581e32d83715" />
<img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/a61c048a-8f6d-4ea3-93e7-782495721c51" />
<img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/1584aa40-536a-4c0a-a4f4-4d4cfde23572" />

## Getting Started
First off, this is a Linux program, which means that Windows by default isn't supported. Secondly, while we have put in work to support multiple different Linux Distros, only a few have actually been tested as working.
Therefore we advise you stick to the tested distros, unless you want to potentially have to manually install dependencies.
### Supported Distros
| Distro             | Status                                                             |
| ----------------- | ------------------------------------------------------------------ |
| Arch Linux (Manjaro & CachyOS) | :white_check_mark: Tested and Working |
| Debian (Ubuntu) | :white_check_mark: Tested and Working |
| Fedora | :warning: Untested |
| OpenSuse | :warning: Untested |

### Installation
Getting started with VirtuNet is straightforward. VirtuNet comes packaged with an Install script that will take care of the initial setup.
However, you will need to install Python 3.13 before the installation will be able to take place.

**If the install script fails to install certain dependencies, you will have to find and install them yourself**

```sh
# Fetch and Install Python3.13
# This varies by Distro, figure it out yourself.

# Open a terminal and pull the newest version:
git clone https://github.com/Lasse-NP/VirtuNet

# CD into the folder:
cd VirtuNet

# Run the install.sh script:
sudo chmod +x install.sh && ./install.sh

# Start the program:
sudo virtunet
```

## Usage
VirtuNet allows for a variety of different virtual devices to be added to the network. You will be able to customize the structure of the network within the Session Settings page. VirtuNet even allows more granular customization by using the Custom Setup page, accessed through the Customize button. On this page you are allowed to change individual settings for each device, allowing full control to build devices outside of the standard templates.

<p align="center"> <img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/f9ade818-a1e7-4b5b-83a1-581e32d83715" />
<img width="318" height="auto" alt="image" src="https://github.com/user-attachments/assets/cfc7df95-6ee5-4d91-95ce-318ca47f8274" /> </p>

After having chosen an assortment of devices, you can now start the server, which in turn starts the virtual network. To allow clients to scan the virtual network, they first have to join the server. This is done by using the Windows Client from the [VirtuNet-Client](https://github.com/Lasse-NP/VirtuNet-Client) project. This is specifically made to work with this program and therefore allows for a simple join code connection flow. Therefore to connect clients to the server, all you have to do is give them the Join Code displayed, along with the IP and Port of the server.

<p align="center"> <img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/a61c048a-8f6d-4ea3-93e7-782495721c51" /> </p>

After connecting the clients to the server, they will now be able to scan the devices on the virtual Network. To help manage and control the virtual Network, the program comes with a Control Panel page, that gives the ability to view statistics about each virtual device, along with buttons to toggle on and off the devices.

<p align="center"> <img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/d9104e58-9c21-49fa-9084-798a1e4a828d" /> 
<img width="200" height="auto" alt="image" src="https://github.com/user-attachments/assets/e3c4621c-41e2-4e50-8548-b9f24b3fe7cb" />
</p>

The Control Panel has a few different buttons. The Trainees button redirects you back to the clients list. The Reset button resets the status of all devices back to online. The Reboot button tears down the virtual network and builds it back up again with the same structure, allowing for a quick network rebuild.

## Dependencies
If the install.sh fails to automatically install the program, more manual means are necessary to complete the installation. Therefore we provide the list below of dependencies that VirtuNet requires to work:
- Python 3.13
- OpenVPN
- OVSwitch (Openvswitch-switch + Openvswitch-testcontroller)
- EasyRSA
- MiniNet
- AvahiDNS
- Libnetfilter-queue
- xcb-util-cursor
- build-essentials
  - gcc
  - makepkg
