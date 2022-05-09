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
  println_green "${RED}Usage: sudo %s -m <IO|XIO|X1> [-n] [-s] [-t] [-d] [-k] [-o]" "$0"
  println_green " - n for NodeRed"
  println_green " - s for Supervisor"
  println_green "These will only affect ${PWD}/andinopy/andinopy_cfg/default.cfg"
  println_green "If you install with supervisor, supervisor will use this configuration"
  println_green " - t for Temp Sensor      Only X1"
  println_green " - d for Nextion Display  Only IO"
  println_green " - k for RFID-Keyboard    Only IO"
  println_green " - o for OLED             Only IO"

  exit 1
  }

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
	println_red "Script must be run as root!"
	usage
fi

if [ ! -w "${PWD}" ]; then
  println_red "Directory is not writable!"
  usage
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


println_red "!!! Installation started !!!"
# update & upgrade
println_green "Updating & upgrading packages..."

sudo apt-get update
sudo apt-get upgrade -y

# install software
println_green "Installing software..."
sudo apt-get install -y minicom screen elinks git
sudo apt-get install -y python3 python3-dev build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev python3-pip libjpeg-dev
### i2c-tools is installed in RTC section



## edit /boot/config.txt
println_green "Enabling I2C, UART, SPI and CAN..."

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
fi;

# install SPI overlay
if [ "$mode" = "IO" ] ; then
  println_green "Installing SPI overlay..."
  wget https://github.com/andino-systems/Andino/raw/master/Andino-IO/BaseBoard/sc16is752-spi0-ce1.dtbo
  sudo cp sc16is752-spi0-ce1.dtbo /boot/overlays/
  echo "dtoverlay=sc16is752-spi0-ce1,int_pin=24,xtal=11059200" | sudo tee -a /boot/config.txt
fi;

if [ "$mode" = "IO" ] ; then
  echo "# CAN on SPI 0.0" | sudo tee -a /boot/config.txt
  echo "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25" | sudo tee -a /boot/config.txt

  println_green "Setting up CAN Bus..."
  sudo ip link set can0 up type can bitrate 125000
  sudo ifconfig can0
fi;


if [ "$mode" = "X1" ] ; then
  echo "# DS1820 Temp sensor" | sudo tee -a /boot/config.txt
  echo "dtoverlay=w1-gpio-pullup,gpiopin=22,extpullup=on" | sudo tee -a /boot/config.txt
  echo "dtoverlay=w1-gpio,gpiopin=22" | sudo tee -a /boot/config.txt
fi;


println_green "Disabling console on /dev/serial0..."
cut -d ' ' -f 3- < /boot/cmdline.txt | sudo tee /boot/cmdline.txt1
mv /boot/cmdline.txt1 /boot/cmdline.txt



# configure RTC
println_green "Setting up RTC..."
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
  println_green "Setting up NodeJS & NodeRed..."
  sleep 1

  println_green "Starting installation. PLEASE CONFIRM WITH 'y' IF PROMPTED."
  bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --confirm-install --confirm-pi --confirm-root

  println_green "Enabling Node-Red in systemctl..."
  sudo systemctl enable nodered.service

  println_red "The Node-Red web UI is currently unsecured!\nFor documentation on how to enable username/password authentication, please refer to:\n https://andino.systems/programming/nodered."

  println_green "Installing custom NodeRed nodes..."

  sudo npm install node-red-contrib-andinox1
  sudo npm install node-red-contrib-andino-sms
  sudo npm install node-red-contrib-andinooled

fi;


# install andinopy
println_green "Setting up Andino Python Library..."

## prerequisites
println_green "Installing prerequisites..."
sudo apt-get install -y libopenjp2-7 libtiff5 fonts-firacode

println_green "Installing font..."
mkdir firacode_inst
cd firacode_inst || exit
wget https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip
unzip Fira_Code_v6.2.zip
sudo mkdir -p /usr/share/fonts/truetype
sudo cp ttf/FiraCode-Regular.ttf  /usr/share/fonts/truetype/FIRACODE.TTF
cd ..

## download and unzip
println_green "Installing wheel..."
sudo pip3 install wheel pyserial

println_green "Downloading and installing andinopy library..."
mkdir andinopy
cd andinopy || exit
wget https://github.com/andino-systems/andinopy/raw/main/dist/andinopy-0.2-py3-none-any.whl
sudo pip3 install andinopy-0.2-py3-none-any.whl
cd ..

# download config file

println_green "Editing Configuration File..."
cd andinopy || exit
mkdir andinopy_cfg
mkdir andinopy_log
cd andinopy_cfg || exit


echo " # This config was automatically generated by andinopy setup.sh
[andino_tcp]
port=9999
tcp_encoding=utf-8
display_encoding=iso-8859-1
shutdown_script=bash -c \"sleep 5; sudo shutdown -h now 'ANDINOPY - SHUTDOWN PIN'\"&
shutdown_duration=6"| sudo tee -a generated.cfg
## HARDWARE MODE
if [ "${mode}" = "IO" ] ; then
  echo "hardware=io"| sudo tee -a generated.cfg
fi
if [ "${mode}" = "XIO" ] ; then
  echo "hardware=io"| sudo tee -a generated.cfg
fi
if [ "${mode}" = "X1" ] ; then
  echo "hardware=x1"| sudo tee -a generated.cfg
fi
#OLED
if [ "${installOled}" = "1" ] ; then
  echo "oled=True"| sudo tee -a generated.cfg
else
  echo "oled=False"| sudo tee -a generated.cfg
fi


#TEMP
if [ "${installTemp}" = "1" ] ; then
  echo "temp=True"| sudo tee -a generated.cfg
else
  echo "temp=False"| sudo tee -a generated.cfg
fi

#KEY_RFID
if [ "${installKeyRfid}" = "1" ] ; then
  echo "key_rfid=True"| sudo tee -a generated.cfg
else
  echo "key_rfid=False"| sudo tee -a generated.cfg
fi

#NEXTION_DISPLAY
if [ "${installDisplay}" = "1" ] ; then
  echo "display=True"| sudo tee -a generated.cfg
else
  echo "display=False"| sudo tee -a generated.cfg
fi

## TODO pins and RELS for XIO
echo "[andino_io]
# inputs
input_pins=13, 19, 16, 26, 20, 21
relay_pins=5, 6, 12
input_pull_up=False,False,False,False,False,False
inputs_polling_time=0.005, 0.005, 0.005, 0.005, 0.005, 0.005
# changes to debounce time currently have no effect
inputs_debounce_time=0.005, 0.005, 0.005, 0.005, 0.005, 0.005
# outputs
relays_start_config=False,False,False
relays_active_high=False,False,False

# Power-fail pin. shutdown_script will activate when pin_power_fail is active for more than shutdown_duration s.
# Python will stop
pin_power_fail=18


[io_x1_emulator]
send_broadcast=True
send_counter=True
send_rel=False
send_on_change=False
change_pattern=1,1,1,1,1,1
send_interval=3000
polling=10
skip=0
debounce=3

[oled]
# if rotate is 1 the image will be rotated by 180 degrees
rotate=0" | sudo tee -a generated.cfg
if [ "${mode}" = "X1" ] ; then
  echo  "[andino_x1]
  shutdown_input_index=2" | sudo tee -a generated.cfg
fi
cd ../.. || exit


# finish and remove script
if [ "${installSupervisor}" = "1" ] ; then
  println_green "Installing Supervisor..."
  sudo apt-get install -y supervisor
  sudo chmod +x /etc/init.d/supervisor
  sudo systemctl daemon-reload
  sudo update-rc.d supervisor defaults
  sudo update-rc.d supervisor enable
  sudo service supervisor start
  echo "[program:andinopy]
command=sudo python3 /usr/local/lib/python3.9/dist-packages/andinopy/__main__.py ${PWD}/andinopy/andinopy_cfg/generated.cfg
directory= ${PWD}
user=root
autostart=true
autorestart=true
startsec=3
redirect_stderr=true
stdout_logfile=${PWD}/andinopy/andinopy_log/andinopy.stdout.txt
stdout_logfile_maxbytes=200000
stdout_logfile_backups=1
priority=900" | sudo tee -a /etc/supervisor/conf.d/andinopy.conf
  cd .. || exit
fi;


println_green "Setup complete! Please reboot to finish.\n"





