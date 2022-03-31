import sys
import time


def test_modules():
    try:
        import gpiozero
    except ImportError:
        print("missing lib 'gpiozero'")
        exit(1)
    try:
        import smbus2
    except ImportError:
        print("missing lib 'smbus'")
        exit(1)
    try:
        import serial
    except ImportError:
        print("missing lib 'smbus'")
        exit(1)
    try:
        import adafruit_ssd1306
    except ImportError:
        print("missing lib 'adafruit-circuitpython-ssd1306'")
        exit(1)
    try:
        import PIL
    except ImportError:
        print("missing lib 'Pillow'")
        exit(1)
    try:
        import busio
    except ImportError:
        print("missing lib 'adafruit-blinka'")
        exit(1)
    try:
        import setuptools
    except ImportError:
        print("missing lib 'setuptools'")
        exit(1)
    try:
        import wheel
    except ImportError:
        print("missing lib 'wheel'")
        exit(1)
    try:
        import andinopy
    except ImportError:
        print("missing lib 'andinopy' - install the library please")
        exit(1)


def test_rels():
    import andinopy.base_devices.andinoio
    andino = andinopy.base_devices.andinoio.andinoio()
    try:
        andino.start()
        print("Set relays to 1")
        for i in range(len(andino.outRel)):
            andino.set_relay(i, 1)
        time.sleep(0.2)
        for i in range(len(andino.outRel)):
            if andino.outRel[i].value != 1:
                print(f"Relays {i} did not change Value to 1")
                exit(1)
        print("Set relays to 0")
        for i in range(len(andino.outRel)):
            andino.set_relay(i, 0)
        time.sleep(0.2)
        for i in range(len(andino.outRel)):
            if andino.outRel[i].value != 0:
                print(f"Relays {i} did not change Value to 0")
                exit(1)
    finally:
        andino.stop()
        del andino


def test_rfid_key():
    from andinopy.base_devices.rfid_keyboard.rfid_keyboard_i2c import rfid_keyboard_i2c
    keybr = rfid_keyboard_i2c()
    real = []
    def keyboard_button(char):
        print(char, end="")
        real.append(char)

    rfids = []

    def on_rfid(rfid):
        print(rfid)
        rfids.append(rfid)

    keybr.on_keyboard_button = keyboard_button
    keybr.on_function_button = keyboard_button
    keybr.on_rfid_string = on_rfid

    try:
        keybr.start()
        try:
            while (keybr._interrupt.active_time > 0):
                keybr._read_i2c()
                time.sleep(0.01)
        except TypeError:
            pass
        expected = [str(i) for i in range(0, 10)]

        print("Press Buttons 0 to 9 in ascending order")
        while len(real) != len(expected):
            pass
        if real != expected:
            print(f"Button Values: {real} - did not match expected: {expected}")
            exit(0)
        print()
        real = []
        expected = ["F" + str(i) for i in range(1, 7)]
        print("Press Buttons F1 to F6 in ascending order")
        while len(real) != len(expected):
            pass
        if real != expected:
            print(f"Button Values: {real} - did not match expected: {expected}")
            exit(0)
        print()

        keybr.buzz_display(1000)
        if input("Did you hear the buzz? y/n").split()[0] != "y":
            print("Buzzer not working")
            exit(0)

        print("Scan RFID-Card")
        while len(rfids) == 0:
            time.sleep(0.1)

        if input(f"Is {rfids[0]} the correct rfid chip? y/n").split()[0] != "y":
            print("RFID not working")
            exit(0)

    finally:
        keybr.stop()







def test_display():
    from andinopy.base_devices.nextion_display import display
    nextion = display()
    try:
        nextion.start()
        nextion.reset()
        nextion.set_text("z0", "Test Text")
        if input(f"Is The Top Line Displaying 'Test Text'? y/n?").split()[0] != "y":
            print("Display not working")
            exit(0)
        nextion.set_attr("z0", "pco", "255")
        if input(f"Is the Text blue now? y/n?").split()[0] != "y":
            print("Display not working")
            exit(0)
    finally:
        nextion.stop()


def test_rtc():
    import os
    os.system('sudo hwclock -r')
    if input(f"Is this the correct Date? y/n?").split()[0] != "y":
        print("RTC not working")
        exit(0)


if __name__ == "__main__":
    if not sys.platform.startswith("linux"):
        print("Das ist ein Program zum Testen des Terminals - Auf Windows funktioniert das nicht")

    print("STEP 1 --- Librarys installiert?")
    test_modules()
    print("All Librarys installed!")



    print("STEP 2 --- Teste IO")
    test_rels()
    print("IO is configured")

    print("STEP 3 --- Teste Buttons")
    test_rfid_key()


    print("STEP 6 --- Display")
    if input(f"Do you see the standard Display? y/n").split()[0] != "y":
        print("Please check the connections to the display and install the Terminal Nextion Image")
        exit(1)
    test_display()

    print("STEP 7 --- RTC")
    test_rtc()

    print("SUCESS --- Terminal working")
