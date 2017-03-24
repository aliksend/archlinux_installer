# Script for semiautomatic installing ArchLinux

This small script helps install and configure archlinux.
You just need:
- download archlinux.iso from official website, burn to cd or usb and boot
- login to livecd, retrieve ip and enable sshd
- wait for installation and than reboot
- remove installation media
- login to new system
- provide hostname, username, timezone and list of necessary packages for new system
- wait for configuring

The script will:
- Partition hard drive (100M for boot, ~2Gb for swap, rest for root)
- Install yandex mirror as first (useful for CIS countries)
- Install system, generate fstab, configure grub, adding ru_RU.UTF-8 locale, adding necessary lines to mkinicpio.conf, enable sshd and dhcpcd

After reboot, script will:
- Set hostname, timezone, localizing system to ru_RU.UTF-8
- Configure pacman to use multilib (only for x64)
- Create user, update system, install necessary packages (provided by user; also will install `yajl` and `bash-completion`), install X11 packages (`xorg-server` `xorg-xinit` `xorg-server-utils` `mesa-libgl`), drivers for videocards (`xf86-video-intel` `xf86-video-ati` `xf86-video-nouveau` `xf86-video-vesa` and `lib32-mesa-libgl` only for x64), Xfce (`xfce4` `xfce4-goodies`), fonts (`ttf-liberation` `ttf-dejavu` `opendesktop-fonts` `ttf-bitstream-vera` `ttf-arphic-ukai` `ttf-arphic-uming` `ttf-hanazono`)
- Configure sudo (`%wheel ALL=(ALL) ALL`)
- Install yaourt
- Allow to use ssh only to created user

## Requirements
- Installed python v2
- Installed `paramiko` (`pip install paramiko`)

## Run script
```
python2 run.py
```

#### Inspired by [this article](https://ziggi.org/ustanovka-i-nastroyka-arch-linux-xfce-chast-1/)