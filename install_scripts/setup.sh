#!/bin/bash
# Andino IO setup script by Christian Drotleff / Jakob Groß @ ClearSystems GmbH, 2022
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

println_green (){
  printf "${GREEN}%s${NC}\n" "${1}"
}

println_red (){
  printf "${RED}%s${NC}\n" "${1}"
}

println (){
  printf "%s\n" "${1}"
}


usage() {
  println_green "${RED}Usage: sudo %s -m <IO|XIO|X1> [-n] [-s] [-t] [-d] [-k] [-o]" "$0";
  println_green " - n for NodeRed";
  println_green " - s for Supervisor";
  println_green "These will only affect ${PWD}/andinopy/andinopy_cfg/default.cfg"
  println_green "If you install with supervisor, supervisor will use this configuration"
  println_green " - t for Temp Sensor      (only configures default.cfg in ";
  println_green " - d for Nextion Display  (only takes effect when supervisor is installed with this script)";
  println_green " - k for RFID-Keyboard    (only takes effect when supervisor is installed with this script)";
  println_green " - o for OLED             (only takes effect when supervisor is installed with this script)";

  exit 1; }



installNodeRed="0"
installSupervisor="0"
installTemp="0"
installDisplay="0"
installKeyRfid="0"
installOled="0"

while getopts ":m:nstdko" opt
do
		case $opt in
				m) mode=${OPTARG}; ((mode == "IO" || mode  == "XIO" || mode == "X1")) || usage;;
        n) installNodeRed="1" ;;
        s) installSupervisor="1";;
        t) installTemp="1";;
        d) installDisplay="1";;
        k) installKeyRfid="1";;
        o) installOled="1";;
				*) usage;;
		esac
done
shift $((OPTIND-1))
if [ -z "${mode}" ]; then usage; fi;

if [ "$(id -u)" -ne 0 ]; then
	println_red "Script must be run as root!}"
	usage
	exit 1
fi

println "#### Andinopy setup script ####"
println "installing NodeRed:             ${installNodeRed}"
println "installing Supervisor:          ${installSupervisor}"
println "installing Temperature Sensor:  ${installTemp}"
println "installing Nextion Display:     ${installDisplay}"
println "installing Keyboard RFID:       ${installKeyRfid}"
println "installing OLED:                ${installOled}"

for i in 5 4 3 2 1
do
  println_green "----- starting in ${i} Seconds press Ctrl+C to cancel -----"
  sleep 1
done
println "!!! Installation started !!!"
# update & upgrade
println "Updating & upgrading packages..."

sudo apt-get update
sudo apt-get upgrade -y

# install software
println "Installing software..."
sudo apt-get install -y minicom screen elinks git
sudo apt-get install -y python3 python3-dev build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev python3-pip libjpeg-dev
### i2c-tools is installed in RTC section

# install SPI overlay
if [ "$mode" = "IO" ] || [ "$mode" = "X1" ] ; then
  println "Installing SPI overlay..."
  wget https://github.com/andino-systems/Andino/raw/master/Andino-IO/BaseBoard/sc16is752-spi0-ce1.dtbo
  sudo cp sc16is752-spi0-ce1.dtbo /boot/overlays/
fi;

## edit /boot/config.txt
println "Enabling I2C, UART, SPI and CAN..."

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

  println "Setting up CAN Bus..."
  sudo ip link set can0 up type can bitrate 125000
  sudo ifconfig can0
fi;


if [ "$mode" = "X1" ] ; then
  echo "# DS1820 Temp sensor" | sudo tee -a /boot/config.txt
  echo "dtoverlay=w1-gpio-pullup,gpiopin=22,extpullup=on" | sudo tee -a /boot/config.txt
  echo "dtoverlay=w1-gpio,gpiopin=22" | sudo tee -a /boot/config.txt
fi;


println "Disabling console on /dev/serial0..."
cut -d ' ' -f 3- < /boot/cmdline.txt | sudo tee /boot/cmdline.txt1
mv /boot/cmdline.txt1 /boot/cmdline.txt



# configure RTC
println "Setting up RTC..."
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
  println "Setting up NodeJS & NodeRed..."
  sleep 1

  println "Starting installation. PLEASE CONFIRM WITH 'y' IF PROMPTED."
  bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --confirm-install --confirm-pi

  println "Enabling Node-Red in systemctl..."
  sudo systemctl enable nodered.service

  println_red "The Node-Red web UI is currently unsecured!\nFor documentation on how to enable username/password authentication, please refer to https://andino.systems/programming/nodered."

  println "Installing custom NodeRed nodes..."

  npm install node-red-contrib-andinox1
  npm install node-red-contrib-andino-sms
  npm install node-red-contrib-andinooled

fi;


# install andinopy
println "Setting up Andino Python Library..."

## prerequisites
println "Installing prerequisites..."
sudo apt-get install -y libopenjp2-7 libtiff5 fonts-firacode

println "Installing font..."
mkdir firacode_inst
cd firacode_inst || exit
wget https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip
unzip Fira_Code_v6.2.zip
sudo mkdir -p /usr/share/fonts/truetype
sudo cp ttf/FiraCode-Regular.ttf  /usr/share/fonts/truetype/FIRACODE.TTF
cd ..

## download and unzip
println "Installing wheel..."
sudo pip3 install wheel pyserial

println "Downloading and installing andinopy library..."
mkdir andinopy
cd andinopy || exit
wget https://github.com/andino-systems/andinopy/raw/main/dist/andinopy-0.2-py3-none-any.whl
sudo pip3 install andinopy-0.2-py3-none-any.whl
cd ..

# download config file

println "Editing Configuration File..."
cd andinopy || exit
mkdir andinopy_cfg
mkdir andinopy_log
cd andinopy_cfg || exit
## TODO dynamic andinopy config
wget https://raw.githubusercontent.com/andino-systems/andinopy/main/andinopy/default.cfg
cd ..\.. | exit


# finish and remove script
if [ "${installSupervisor}" = "1" ] ; then
  println "Installing Supervisor..."
  sudo apt-get install -y supervisor
  sudo chmod +x /etc/init.d/supervisor
  sudo systemctl daemon-reload
  sudo update-rc.d supervisor defaults
  sudo update-rc.d supervisor enable
  sudo service supervisor start



  echo "[program:andinopy]
command=sudo python3 /usr/local/lib/python3.9/dist-packages/andinopy/__main__.py ${PWD}/andinopy/andinopy_cfg/default.cfg
directory= ${PWD}
user=root
autostart=true
autorestart=true
startsec=3
redirect_stderr=true
stdout_logfile=${PWD}/andinopy_log/andinopy.stdout.txt
stdout_logfile_maxbytes=200000
stdout_logfile_backups=1
priority=900" | sudo tee -a /etc/supervisor/conf.d/andinopy.conf
  cd ..
fi;


printf "Setup complete! Please reboot to finish.\n"





