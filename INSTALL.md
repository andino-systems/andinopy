## Installation

### Easy Mode
This will use an installation script to install & configure:
  - Necessary overlays and software for Andino board
  - Andinopy with all requirements
  - NodeRed with all Andino Nodes
  - Supervisor for andinopy autostart

```shell
wget https://raw.githubusercontent.com/andino-systems/andinopy/main/install_scripts/setup.sh
chmod +x setup.sh
sudo ./setup.sh -m IO -n 1 -s 1
```
Change `IO` to `X1` or `XIO` for other Hardware Versions.

* Set -n if you want to install NodeRed.
* Set -s if you want to install Supervisor (recommended! If you choose not to install it, you will need to set up Andinopy-TCP another way if you want to use NodeRed).
* Set -o if you want to use the OLED display functionality (Andino IO, XIO)
* Set -t if you want to use a temperature sensor (Andino X1 only!)
* Set -d if your device has a Nextion Display (Andino Terminal only!)
* Set -k if your device has a RFID reader/keyboard (Andino Terminal only!)

### Manual Installation
Follow the steps according to your Hardware (IO, XIO or X1)

**1. Install python3 (IO, XIO, X1)**
```shell
sudo apt install python3 python3-pip python-serial
```

**2. Install SPI overlay (IO, XIO)**
```shell
wget https://github.com/andino-systems/Andino/raw/master/Andino-IO/BaseBoard/sc16is752-spi0-ce1.dtbo
sudo cp sc16is752-spi0-ce1.dtbo /boot/overlays/
```

**3. Append the following to /boot/config.txt (IO, XIO, X1)**
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
**4. Add the following to /etc/modules-load.d/modules.conf (IO, XIO, X1)**
```shell
i2c-dev
```
**5. Disable Console on Serial0 (IO, XIO, X1)**
```shell
cut -d ' ' -f 3- < /boot/cmdline.txt | sudo tee /boot/cmdline.txt
```

**6. Set Up Can BUS (IO, XIO, X1)**
```shell
sudo ip link set can0 up type can bitrate 125000
sudo ifconfig can0
```

**7. Set Up RTC (IO, XIO, X1)**
```shell
sudo apt-get install -y i2c-tools
sudo apt-get purge -y fake-hwclock
sudo apt-get remove fake-hwclock -y 
sudo dpkg --purge fake-hwclock 
sudo rm -f /etc/adjtime.
sudo cp /usr/share/zoneinfo/Europe/Berlin /etc/localtime
sudo ln -s /home/pi/bin/ntp2hwclock.sh /etc/cron.hourly/ntp2hwclock
```

**7. Install Node Red (Optional) (IO, XIO, X1)**
```shell
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered) --confirm-install --confirm-pi
sudo systemctl enable nodered.service

npm install node-red-contrib-andinox1
npm install node-red-contrib-andino-sms
npm install node-red-contrib-andinooled
```

**8. Install Andinopy (IO, XIO, X1)**

Prerequisites:
```shell
sudo apt install libopenjp2-7 libtiff5 fonts-firacode
mkdir firacode_inst
cd firacode_inst
wget https://github.com/tonsky/FiraCode/releases/download/6.2/Fira_Code_v6.2.zip
unzip Fira_Code_v6.2.zip
sudo mkdir -p /usr/share/fonts/truetype
sudo cp ttf/FiraCode-Regular.ttf  /usr/share/fonts/truetype/FIRACODE.TTF
cd ..
```
Installing wheel:
```shell
sudo pip3 install wheel pyserial
```
Download and install andinopy:
```shell
git clone https://github.com/andino-systems/andinopy.git
cd andinopy
sudo pip3 install ./dist/andinopy-0.2-py3-none-any.whl
```
Edit the config file at *./andinopy/default.cfg* to set your board paramaters. For basic usage, it should be sufficient to change the values in the andino_tcp section to your hardware configuration. At hardware=... you can change your board configuration. Valid options are *io* for Andino IO / Andino XIO and *x1* for Andino X1.

	hardware=io

The following individual parameters should be set to True if:

	oled - Your board has an oled display
	temp - You want to connect a [Temperature sensor](/andino-x1/ds18b20-sensors) to your board
	key_rfid - Your hardware has an RFID-Reader (Andino Terminal)
	display - Your hardware has a Nextion Display (Andino Terminal)


**9. Enable Andinopy with Supervisor as Standalone**
```shell
sudo apt install supervisor
sudo chmod +x /etc/init.d/supervisor
sudo systemctl daemon-reload
sudo update-rc.d supervisor defaults
sudo update-rc.d supervisor enable
sudo service supervisor start
```

Add andinopy entry to configuration file:

```shell
sudo nano /etc/supervisor/conf.d/andinopy.conf
```
Add the following lines:

```shell
[program:andinopy]
command=sudo python3 /usr/local/lib/python3.9/dist-packages/andinopy/__main__.py [install_dir]/andinopy/andinopy_cfg/generated.cfg
directory= [install_dir]
user=root
autostart=true
autorestart=true
startsec=3
redirect_stderr=true
stdout_logfile=[install_dir]/andinopy/andinopy_log/andinopy.stdout.txt
stdout_logfile_maxbytes=200000
stdout_logfile_backups=1
priority=900
```

Replace [install_dir] (at the options command, directory and stdout_logfile) with the directory that andinopy is installed in

**10. Or use Andinopy modules for your own projects i.e.**

```python
import andinopy
import andinopy.base_devices.nextion_display

display = andinopy.base_devices.nextion_display.display()
display.start()

display.set_text("myObj", "myTestText") # set myObj txt to "myTestText
display.set_attr("myObj","pco", "255") # set myObj fontcolor to blue
```



