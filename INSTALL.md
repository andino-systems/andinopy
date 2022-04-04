## Installation

### Easy Mode
This will use an installation script to install & configure:
  - Necessary overlays and software for Andino board
  - Andinopy with all requirements
  - NodeRed with all Andino Nodes
  - Supervisor for andinopy autostart
  
#### Andino-IO
```shell
TODO install with or without Nodered
```
#### Andino-XIO
```shell
TODO install with or without Nodered
```
#### Andino-X1
```shell
TODO install with or without Nodered
```

### Manual Installation
Follow the steps according to your Hardware (IO, XIO or X1)

1. Install python3 (IO, XIO, X1)
```shell
sudo apt install python3 python3-pip python-serial
```

2. Install SPI overlay (IO, XIO)
```shell
wget https://github.com/andino-systems/Andino/raw/master/Andino-IO/BaseBoard/sc16is752-spi0-ce1.dtbo
sudo cp sc16is752-spi0-ce1.dtbo /boot/overlays/
```

3. Append the following to /boot/config.txt (IO, XIO, X1)
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
4. Add the following to /etc/modules-load.d/modules.conf (IO, XIO, X1)
```shell
i2c-dev
```
5. Disable Console on Serial0 (IO, XIO, X1)
```shell
cut -d ' ' -f 3- < /boot/cmdline.txt | sudo tee /boot/cmdline.txt
```

6. Set Up Can BUS (IO, XIO, X1)
```shell
sudo ip link set can0 up type can bitrate 125000
sudo ifconfig can0
```

7. Set Up RTC (IO, XIO, X1)
```shell
sudo apt-get install -y i2c-tools
sudo apt-get purge -y fake-hwclock
sudo apt-get remove fake-hwclock -y 
sudo dpkg --purge fake-hwclock 
sudo rm -f /etc/adjtime.
sudo cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime
sudo ln -s /home/pi/bin/ntp2hwclock.sh /etc/cron.hourly/ntp2hwclock
```

7. Install Node Red (Optional) (IO, XIO, X1)
```shell
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --confirm-install --confirm-pi
sudo systemctl enable nodered.service

npm install node-red-contrib-andinox1
npm install node-red-contrib-andino-sms
npm install node-red-contrib-andinooled
```

8. Install Andinopy (IO, XIO, X1)
```shell
TODO
```

9. Enable Andinopy with Supervisor as Standalone
```shell
TODO
```

10. Or use Andinopys modules for your own projects ie.

#### Nextion Display
```python
import andinopy
import andinopy.base_devices.nextion_display

display = andinopy.base_devices.nextion_display.display()
display.start()

display.set_text("myObj", "myTestText") # set myObj txt to "myTestText
display.set_attr("myObj","pco", "255") # set myObj fontcolor to blue
```

#### Andino IO or XIO
```python
import andinopy.base_devices.andinoio

# set PINS in default.cfg
io_device = andinopy.base_devices.andinoio.andinoio()
io_device.input_pins
```