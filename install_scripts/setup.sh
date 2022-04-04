#!/bin/bash
# Andino IO setup script by Christian Drotleff / Jakob Groß @ ClearSystems GmbH, 2022

usage() { printf "Usage: sudo %s -m <IO|XIO|X1> [-n <1|0>] [-s <1|0>] \n - n for NodeRed \n - s for Supervisor" "$0" 1>&2; exit 1; }

installNodeRed=0
installSupervisor=0
while getopts ":m:n:s:" opt
do
		case $opt in
				m) mode=${OPTARG}; ((mode == "IO" || mode  == "XIO" || mode == "X1")) || usage;;
        n) installNodeRed=${OPTARG}; ((installNodeRed == "1" || installNodeRed  == "0")) || usage;;
        s) installSupervisor=${OPTARG}; ((installSupervisor == "1" || installSupervisor  == "0")) || usage;;
				*) usage;;
		esac
done
shift $((OPTIND-1))
if [ -z "${mode}" ]; then usage; fi;
if [ "$(id -u)" -ne 0 ]; then
	printf "Script must be run as root.\n"
	usage
	exit 1
fi

printf "#### Andinopy setup script ####\n"
printf "installing for %s, NodeRed: %s, Supervisor: %s" "$mode" "$installNodeRed" "$installSupervisor"
printf "starting in 3 Seconds press Ctrl+C to cancel..."
sleep 3
printf "Installation started"
# update & upgrade
printf "Updating & upgrading packages...\n"

sudo apt-get update
sudo apt-get upgrade -y

# install software
printf "Installing software...\n"
sudo apt-get install -y minicom screen elinks git python3 python3-pip

### i2c-tools is installed in RTC section

# install SPI overlay
if [ "$mode" = "IO" ] || [ "$mode" = "X1" ] ; then
  printf "Installing SPI overlay...\n"
  wget https://github.com/andino-systems/Andino/raw/master/Andino-IO/BaseBoard/sc16is752-spi0-ce1.dtbo
  sudo cp sc16is752-spi0-ce1.dtbo /boot/overlays/
fi;

## edit /boot/config.txt
printf "Enabling I2C, UART, SPI and CAN...\n"

echo "i2c-dev" | sudo tee -a /etc/modules-load.d/modules.conf


echo "# I2C on" | sudo tee -a /boot/config.txt
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
echo "# RTC" | sudo tee -a /boot/config.txt
echo "dtoverlay=i2c-rtc,ds3231" | sudo tee -a /boot/config.txt

echo "# UART" | sudo tee -a /boot/config.txt
echo "enable_uart=1" | sudo tee -a /boot/config.txt
echo "dtoverlay=pi3-disable-bt-overlay" | sudo tee -a /boot/config.txt
echo "dtoverlay=pi3-miniuart-bt" | sudo tee -a /boot/config.txt

if [ "$mode" = "X1" ] || [ "$mode" = "IO" ] ; then
  echo "# SPI on" | sudo tee -a /boot/config.txt
  echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
  echo "# SPI-UART on SPI 0.1" | sudo tee -a /boot/config.txt
  echo "dtoverlay=sc16is752-spi0-ce1,int_pin=24,xtal=11059200" | sudo tee -a /boot/config.txt
fi;

if [ "$mode" = "IO" ] ; then
  echo "# CAN on SPI 0.0" | sudo tee -a /boot/config.txt
  echo "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25" | sudo tee -a /boot/config.txt

  printf "Setting up CAN Bus...\n"
  sudo ip link set can0 up type can bitrate 125000
  sudo ifconfig can0
fi;


if [ "$mode" = "X1" ] ; then
  echo "# DS1820 Temp sensor" | sudo tee -a /boot/config.txt
  echo "dtoverlay=w1-gpio-pullup,gpiopin=22,extpullup=on" | sudo tee -a /boot/config.txt
  echo "dtoverlay=w1-gpio,gpiopin=22" | sudo tee -a /boot/config.txt
fi;


printf "Disabling console on /dev/serial0...\n"
cut -d ' ' -f 3- < /boot/cmdline.txt | sudo tee /boot/cmdline.txt1
mv /boot/cmdline.txt1 /boot/cmdline.txt



# configure RTC
printf "Setting up RTC...\n"
sudo apt-get install -y i2c-tools
sudo apt-get purge -y fake-hwclock
sudo apt-get remove fake-hwclock -y
sudo dpkg --purge fake-hwclock 
sudo rm -f /etc/adjtime.
sudo cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime
mkdir ~/bin/
wget 'https://raw.githubusercontent.com/andino-systems/Andino/master/Andino-Common/src/rtc/ntp2hwclock.sh' -O /home/pi/bin/ntp2hwclock.sh
sudo ln -s ~/bin/ntp2hwclock.sh /etc/cron.hourly/ntp2hwclock

if [ "${installNodeRed}" = "1" ] ; then
  printf "Setting up NodeJS & NodeRed...\n"
  sleep 1

  printf "Starting installation. PLEASE CONFIRM WITH 'y' IF PROMPTED.\n"
  bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --confirm-install --confirm-pi

  printf "Enabling Node-Red in systemctl...\n"
  sudo systemctl enable nodered.service
  printf "...done.\n"

  printf "The Node-Red web UI is currently unsecured!\nFor documentation on how to enable username/password authentication, please refer to https://andino.systems/programming/nodered. \n"

  printf "Installing custom NodeRed nodes...\n"

  npm install node-red-contrib-andinox1
  npm install node-red-contrib-andino-sms
  npm install node-red-contrib-andinooled

fi;


# install andinopy
printf "Setting up Andino Python Library...\n"

## prerequisites
printf "Installing prerequisites...\n"
sudo apt-get install -y libopenjp2-7 libtiff5 fonts-firacode

printf "Installing font...\n"
mkdir firacode_inst
cd firacode_inst || exit
wget https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip
unzip Fira_Code_v6.2.zip
mv FiraCode-Regular.ttf FIRACODE.TTF
sudo mkdir -p /usr/share/fonts/truetype
sudo cp FIRACODE.TTF /usr/share/fonts/truetype/
cd ..

## download and unzip
printf "Installing wheel...\n"
sudo pip3 install wheel pyserial

printf "Downloading and installing andinopy library...\n"
mkdir andinopy_isnt
cd andinopy_isnt || exit
wget https://github.com/andino-systems/andinopy/raw/main/dist/andinopy-0.2-py3-none-any.whl
pip3 install andinopy-0.2-py3-none-any.whl
cd ..

# download config file


# finish and remove script
if [ "${installSupervisor}" = "1" ] ; then
  printf "Installing Supervisor..."
  sudo apt-get install -y supervisor
  sudo chmod +x /etc/init.d/supervisor
  sudo systemctl daemon-reload
  sudo update-rc.d supervisor defaults
  sudo update-rc.d supervisor enable
  sudo service supervisor start

  mkdir andinopy_cfg
  cd andinopy_cfg || exit
  https://raw.githubusercontent.com/andino-systems/andinopy/main/andinopy/default.cfg
  cd ..

  echo "[program:andinopy]
command=sudo python3 /usr/local/lib/python3.7/dist-packages/andinopy/__main__.py
directory= ${PWD}
user=root
autostart=true
autorestart=true
startsec=3
redirect_stderr=true
stdout_logfile=/mnt/ram/andinopy.stdout.txt
stdout_logfile_maxbytes=200000
stdout_logfile_backups=1
priority=900" | sudo tee -a /etc/supervisor/conf.d/andinopy.conf

  printf "change config in andinopy_cfg/default.cfg then reboot"
  exit
fi;


printf "Setup complete! Please reboot to finish.\n"





