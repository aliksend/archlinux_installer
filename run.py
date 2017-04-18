#!/usr/bin/env python2
# coding: utf8
import subprocess
import socket
import time
import sys
import paramiko

device = 'sda'

print("1. Boot to ArchLinux.iso")
ip = raw_input("2. Get IP (run `ip address` of `ifconfig`): ")
print("   Checking ip")

proc = subprocess.Popen(["ping", "-c 1", "-W 100", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
proc.wait()
res = proc.communicate() 
response = proc.returncode
if response != 0:
  print("   Host is down =(")
  exit(1)

print("3. Run `passwd` and set root's password `root`")
print("4. Run `systemctl start sshd`")
print("   Waiting for 22 port")

while True:
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((ip, 22))
		s.close()
		break
	except:
		time.sleep(1)

print("   Connecting")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=ip, username='root', password='root')

### Work using ssh

def dbg_print(text):
	print("--> " + text)

def ssh_exec(command, ignore_exit_code=False):
	stdin, stdout, stderr = client.exec_command(command, get_pty=True)
	while not stdout.closed:
		line = stdout.readline()
		if line == '':
			break
		sys.stdout.write('\033[92m>\033[0m ' + line)

	# stdout_str = stdout.read()
	# if stdout_str != '':
	# 	stdout_lines = stdout_str.splitlines()
	# 	for line in stdout_lines:
	# 		print('\033[92m>\033[0m ' + line)

	stderr_str = stderr.read()
	if stderr_str != '':
		stderr_lines = stderr_str.splitlines()
		for line in stderr_lines:
			print('\033[91m>\033[0m ' + line)

	if not ignore_exit_code:
		exit_status = stdout.channel.recv_exit_status()
		if exit_status != 0:
			print("\033[91m==> FAIL\033[0m {0}".format(exit_status))
			exit(2)

dbg_print("Setting time")
ssh_exec('timedatectl set-ntp true')

dbg_print("Partitioning drive")
ssh_exec('parted /dev/{0} -s -a opt mklabel msdos mkpart primary ext2 0% 100MB set 1 boot on mkpart primary linux-swap 100MB 2048MB mkpart primary ext4 2048MB 100%'.format(device))

dbg_print("Creating filesystems")
ssh_exec('mkfs.ext2 /dev/{0}1 -F -L boot'.format(device))
ssh_exec('mkswap /dev/{0}2 -L swap'.format(device))
ssh_exec('mkfs.ext3 /dev/{0}3 -F -L root'.format(device))

dbg_print("Mounting filesystems")
ssh_exec('mount /dev/{0}3 /mnt'.format(device))
ssh_exec('mkdir /mnt/boot')
ssh_exec('mount /dev/{0}1 /mnt/boot'.format(device))
ssh_exec('swapon /dev/{0}2'.format(device))

dbg_print("Updating mirrors")
ssh_exec('mv /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.orig')
ssh_exec('echo \'Server = http://mirror.yandex.ru/archlinux/$repo/os/$arch\' > /etc/pacman.d/mirrorlist')
ssh_exec('cat /etc/pacman.d/mirrorlist.orig >> /etc/pacman.d/mirrorlist')
ssh_exec('rm /etc/pacman.d/mirrorlist.orig')

dbg_print("Killing SigLevel")
ssh_exec('pacman-key --init')
ssh_exec('sed -i \'s/^SigLevel\s*= Required DatabaseOptional/SigLevel=Never/g\' /etc/pacman.conf')

dbg_print("Installing packages")
ssh_exec('pacstrap /mnt --noconfirm base base-devel net-tools grub openssh')

dbg_print("Generating fstab")
ssh_exec('genfstab -p /mnt > /mnt/etc/fstab')

dbg_print("Localizing new system")
ssh_exec('echo "en_US.UTF-8 UTF-8" >> /mnt/etc/locale.gen')
ssh_exec('echo "ru_RU.UTF-8 UTF-8" >> /mnt/etc/locale.gen')
ssh_exec('arch-chroot /mnt locale-gen')

dbg_print("Adding hooks and modules to mkinitcpio.conf")
ssh_exec('sed -i \'s/^MODULES=""/MODULES="i915 radeon nouveau"/g\' /mnt/etc/mkinitcpio.conf')
ssh_exec('sed -i \'s/^HOOKS="base/HOOKS="base keymap/g\' /mnt/etc/mkinitcpio.conf')

dbg_print("Running mkinitcpio")
ssh_exec('arch-chroot /mnt mkinitcpio -p linux')

dbg_print("Installing grub")
ssh_exec('arch-chroot /mnt grub-install /dev/{0}'.format(device))
ssh_exec('arch-chroot /mnt grub-mkconfig -o /boot/grub/grub.cfg')

dbg_print("Enabling dhcpcd and sshd")
ssh_exec('arch-chroot /mnt systemctl enable dhcpcd')
ssh_exec('arch-chroot /mnt systemctl enable sshd')
ssh_exec('echo "PermitRootLogin yes" >> /mnt/etc/ssh/sshd_config')

dbg_print("Setting root password (`root`)")
stdin, stdout, stderr = client.exec_command('arch-chroot /mnt passwd')
stdin.write('root\n')
stdin.write('root\n')

dbg_print("Umounting drives")
ssh_exec('umount /mnt/boot')
time.sleep(2)
ssh_exec('umount /mnt')
time.sleep(2)
ssh_exec('swapoff /dev/{0}2'.format(device))

raw_input("5. Now remove installation media and press Enter to reboot")

dbg_print("Rebooting")
ssh_exec('reboot', ignore_exit_code=True)

client.close()

## Working in installed system

print("6. Login as root/root")
ip = raw_input("7. Get IP (run `ip address` of `ifconfig`): ")
print("   Checking ip")

proc = subprocess.Popen(["ping", "-c 1", "-W 100", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
proc.wait()
res = proc.communicate() 
response = proc.returncode
if response != 0:
  print("   Host is down =(")
  exit(1)

hostname = raw_input("8. Enter hostname for new system: ")
username = raw_input("9. Enter username for new system: ")
print("   Password will be the same")
timezone = raw_input("10. Enter timezone: ")
packages = raw_input("11. Packages to install: ") # tmux ffmpeg git docker gpm nmon dstat ...

print("   Waiting for 22 port")

while True:
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((ip, 22))
		s.close()
		break
	except:
		time.sleep(1)

print("   Connecting")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname=ip, username='root', password='root')

### Work using ssh
dbg_print("Setting hostname")
ssh_exec('hostnamectl set-hostname ' + hostname)
ssh_exec('systemctl enable systemd-resolved')

dbg_print("Setting time")
ssh_exec('timedatectl set-timezone ' + timezone)
ssh_exec('timedatectl set-ntp true')

dbg_print("Localizing system")
ssh_exec('localectl set-keymap ru')
ssh_exec('setfont cyr-sun16')
ssh_exec('localectl set-locale LANG="ru_RU.UTF-8"')
ssh_exec('export LANG=ru_RU.UTF-8')
ssh_exec('echo "FONT=cyr-sun16" > /etc/vconsole.conf')

dbg_print("Updating mkinitcpio")
ssh_exec('mkinitcpio -p linux')

dbg_print("Updating grub")
ssh_exec('grub-mkconfig -o /boot/grub/grub.cfg')

dbg_print("Getting system architecture")
stdin, stdout, stderr = client.exec_command('grep -q "^flags.*\\blm\\b" /proc/cpuinfo && echo 64 || echo 32')
architecture = stdout.read().strip()

if architecture == "":
	dbg_print("\033[91mERROR! Cannot get system architecture\033[0m")

if architecture == "64":
	dbg_print("Adding multilib to pacman repos list (x64 only)")
	ssh_exec('echo -e \'[multilib]\\nInclude = /etc/pacman.d/mirrorlist\' >> /etc/pacman.conf')

dbg_print("Creating user")
ssh_exec('useradd -m -g users -G audio,games,lp,optical,power,scanner,storage,video,wheel -s /bin/bash ' + username)
stdin, stdout, stderr = client.exec_command('passwd ' + username)
stdin.write(username + '\n')
stdin.write(username + '\n')

dbg_print("Updating keys")
ssh_exec('pacman-key --init')
ssh_exec('pacman-key --populate archlinux')

dbg_print("Updating system")
ssh_exec('pacman --noconfirm -Syyu')

dbg_print("Installing packages")
ssh_exec('pacman --noconfirm -S yajl bash-completion ' + packages) 

packages = 'xorg-server xorg-xinit xorg-server-utils mesa-libgl ' + \
	'xf86-video-intel xf86-video-ati xf86-video-nouveau xf86-video-vesa ' + \
	'xfce4 xfce4-goodies ' + \
	'ttf-liberation ttf-dejavu opendesktop-fonts ttf-bitstream-vera ttf-arphic-ukai ttf-arphic-uming ttf-hanazono '

if architecture == "64":
	packages += 'lib32-mesa-libgl '

dbg_print("Installing X")
ssh_exec('pacman --noconfirm -S ' + packages)

dbg_print("Configuring sudo")
ssh_exec('sed -i \'s/^# %wheel ALL=(ALL) ALL/%wheel ALL=(ALL) ALL/g\' /etc/sudoers')

dbg_print("Installing yaourt")
ssh_exec('mkdir /build')
ssh_exec('echo \'cd /build\' > /build/build.sh')
ssh_exec('echo \'curl -O https://aur.archlinux.org/cgit/aur.git/snapshot/$1.tar.gz\' >> /build/build.sh')
ssh_exec('echo \'tar xzf $1.tar.gz\' >> /build/build.sh')
ssh_exec('echo \'cd $1\' >> /build/build.sh')
ssh_exec('echo \'makepkg\' >> /build/build.sh')
ssh_exec('chmod +x /build/build.sh')
ssh_exec('chown nobody:nobody /build')
dbg_print("  Installing package-query")
ssh_exec('sudo -u nobody /build/build.sh package-query')
ssh_exec('pacman --noconfirm -U /build/package-query/*.pkg.tar.xz')
dbg_print("  Installing package-query")
ssh_exec('sudo -u nobody /build/build.sh yaourt')
ssh_exec('pacman --noconfirm -U /build/yaourt/*.pkg.tar.xz')
dbg_print("  Cleaning up")
ssh_exec('cd /')
ssh_exec('rm -rf /build')

dbg_print("Removing PermitRootLogin from sshd_config and adding " + username)
ssh_exec('sed -i \'s/^PermitRootLogin yes/AllowUsers ' + username + '/g\' /etc/ssh/sshd_config')

print("12. System is installed and configured. Rebooting")
ssh_exec('reboot', ignore_exit_code=True)

client.close()

