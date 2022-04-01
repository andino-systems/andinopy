# Andio.Systems Python Library

## Installation

### Easy Mode
This will use an install script to install & configure:
  - Necessary overlays and software for Andino board
  - Andinopy with all requirements
  - NodeRed with all Andino Nodes
  - Supervisor for andinopy autostart
  
#### Andino-IO
```shell
TODO
```
#### Andino-XIO
```shell
TODO
```
#### Andino-X1
```shell
TODO
```

### Manual Install Andino-IO
1. Install python3
```shell
sudo apt install python3 python3-pip python-serial
```

2. Install SPI overlay
```shell
wget https://github.com/andino-systems/Andino/raw/master/Andino-IO/BaseBoard/sc16is752-spi0-ce1.dtbo
sudo cp sc16is752-spi0-ce1.dtbo /boot/overlays/
```

3. Append the following to /boot/config.txt
```shell
# -----------------------
# Andino IO from here
# -----------------------

# SPI on
dtparam=spi=on

# I2C on
dtparam=i2c_arm=on

# RTC
dtoverlay=i2c-rtc,ds3231

# CAN on SPI 0.0
dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25

# 1. UART
enable_uart=1
dtoverlay=pi3-disable-bt-overlay
dtoverlay=pi3-miniuart-bt

# 2. SPI-UART on SPI 0.1
dtoverlay=sc16is752-spi0-ce1,int_pin=24,xtal=11059200

# DS1820 Temp sensor
dtoverlay=w1-gpio-pullup,gpiopin=22,extpullup=on
dtoverlay=w1-gpio,gpiopin=22
```

4. Disable Console on Serial0
```shell
cut -d ' ' -f 3- < /boot/cmdline.txt | sudo tee /boot/cmdline.txt
```

5. Set Up Can BUs
```shell
sudo ip link set can0 up type can bitrate 125000
sudo ifconfig can0
```

6. Set Up RTC
```shell
sudo apt-get install -y i2c-tools
sudo apt-get purge -y fake-hwclock
sudo apt-get remove fake-hwclock -y 
sudo dpkg --purge fake-hwclock 
sudo rm -f /etc/adjtime.
sudo cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime
sudo ln -s /home/pi/bin/ntp2hwclock.sh /etc/cron.hourly/ntp2hwclock
```

7. Install Node Red (Optional)
```shell
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --confirm-install --confirm-pi
sudo systemctl enable nodered.service
cd ~/.node-red/ 
npm install node-red-contrib-andinox1
npm install node-red-contrib-andino-sms
npm install node-red-contrib-andinooled
cd ~
```

8. Install Andinopy
```shell
TODO
```