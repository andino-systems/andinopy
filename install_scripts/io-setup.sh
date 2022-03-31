# Andino IO setup script by Christian Drotleff @ ClearSystems GmbH, 2022
#!/bin/bash

printf "#### Andino IO setup script ####\n"

# update & upgrade
printf "[IO Setup] Updating & upgrading packages...\n"

sudo apt-get update
sudo apt-get upgrade -y

# install software
printf "[IO Setup] Installing software...\n"
sleep 1
sudo apt-get install -y minicom screen elinks git python python-pip python3 python3-pip python-serial

### i2c-tools is installed in RTC section

# install SPI overlay

wget https://github.com/andino-systems/Andino/raw/master/Andino-IO/BaseBoard/sc16is752-spi0-ce1.dtbo
sudo cp sc16is752-spi0-ce1.dtbo /boot/overlays/

## edit /boot/config.txt
printf "Enabling UART in /boot/config.txt...\n"

echo "# SPI on" | sudo tee -a /boot/config.txt
echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
echo "# I2C on" | sudo tee -a /boot/config.txt
echo "dtparam=i2c_arm=on" | sudo tee -a /boot/config.txt
echo "# RTC" | sudo tee -a /boot/config.txt
echo "dtoverlay=i2c-rtc,ds3231" | sudo tee -a /boot/config.txt
echo "# CAN on SPI 0.0" | sudo tee -a /boot/config.txt
echo "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25" | sudo tee -a /boot/config.txt
echo "# 1. UART" | sudo tee -a /boot/config.txt
echo "enable_uart=1" | sudo tee -a /boot/config.txt
echo "dtoverlay=pi3-disable-bt-overlay" | sudo tee -a /boot/config.txt
echo "dtoverlay=pi3-miniuart-bt" | sudo tee -a /boot/config.txt
echo "# 2. SPI-UART on SPI 0.1" | sudo tee -a /boot/config.txt
echo "dtoverlay=sc16is752-spi0-ce1,int_pin=24,xtal=11059200" | sudo tee -a /boot/config.txt
echo "# DS1820 Temp sensor" | sudo tee -a /boot/config.txt
echo "dtoverlay=w1-gpio-pullup,gpiopin=22,extpullup=on" | sudo tee -a /boot/config.txt
echo "dtoverlay=w1-gpio,gpiopin=22" | sudo tee -a /boot/config.txt

## edit /boot/cmdline.txt

printf "Disabling console on /dev/serial0...\n"
cut -d ' ' -f 3- < /boot/cmdline.txt | sudo tee /boot/cmdline.txt

# CAN Bus

printf "Setting up CAN Bus...\n"
sudo ip link set can0 up type can bitrate 125000
sudo ifconfig can0


# configure RTC
printf "[IO Setup] Setting up RTC...\n"
sudo apt-get install -y i2c-tools
sudo apt-get purge -y fake-hwclock
sudo apt-get remove fake-hwclock -y
sudo dpkg --purge fake-hwclock 
sudo rm -f /etc/adjtime.
sudo cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime
sudo ln -s /home/pi/bin/ntp2hwclock.sh /etc/cron.hourly/ntp2hwclock



printf "[IO Setup] Setting up NodeJS & NodeRed...\n"
sleep 1

printf "Starting installation. PLEASE CONFIRM WITH 'y' IF PROMPTED.\n"
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --confirm-install --confirm-pi

printf "Enabling Node-Red in systemctl...\n"
sudo systemctl enable nodered.service
printf "...done.\n"

printf "The Node-Red web UI is currently unsecured! For documentation on how to enable username/password authentication, please refer to https://andino.systems/programming/nodered. \n"

printf "Installing custom NodeRed nodes...\n"

cd ~/.node-red/ || exit 2
npm install node-red-contrib-andinox1
npm install node-red-contrib-andino-sms
npm install node-red-contrib-andinooled
cd ~ || exit 2

printf "...done.\n"

# install andinopy

printf "[IO Setup] Setting up Andino Python Library...\n"
sleep 1

## prerequisites
printf "Installing prerequisites...\n"
sudo apt-get install -y libopenjp2-7 libtiff5 fonts-firacode

printf "Installing font...\n"
cd ~/tmp || exit 2
wget 'https://raw.githubusercontent.com/tonsky/FiraCode/master/distr/ttf/FiraCode-Regular.ttf'
mv FiraCode-Regular.ttf FIRACODE.TTF
sudo mkdir -p /usr/share/fonts/truetype
sudo cp FIRACODE.TTF /usr/share/fonts/truetype/
cd ~ || exit 2

## download and unzip
printf "Installing wheel...\n"
sudo pip3 install wheel
printf "Downloading andinopy library...\n"

# TODO

## setup
printf "Installing andinopy library...\n"
sudo python3 setup.py bdist_wheel
sudo pip3 install dist/andinopy-0.1-py3-none-any.whl

# finish and remove script

printf "[IO Setup] Setup complete! Please reboot to finish.\n"
rmdir /home/pi/tmp
rm /home/pi/io-setup.sh




