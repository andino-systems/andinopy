import logging
import multiprocessing
import resource
import sys
import threading
import time
import andinopy
import gpiozero
from gpiozero.pins.mock import MockFactory

import andinopy
from andinopy.tcp.andino_tcp import andino_tcp

andinopy.initialize_cfg("default.cfg")

log = logging.getLogger("andinopy")
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)



if sys.platform.startswith("win"):
    gpiozero.Device.pin_factory = MockFactory()
server = andino_tcp()
try:

    server.start()
    print("andino server started on port 9999")
    cores = multiprocessing.cpu_count()
    usage = resource.getrusage(resource.RUSAGE_SELF)
    user_time = usage.ru_utime
    total_user_time = user_time
    system_time = usage.ru_stime
    total_system_time = system_time
    debug_timer=10
    while 1:
        time.sleep(debug_timer)
        if andinopy.andinopy_logger.isEnabledFor(logging.DEBUG):
            usage = resource.getrusage(resource.RUSAGE_SELF)
            user_time = usage.ru_utime - total_user_time
            total_user_time = usage.ru_utime
            system_time = usage.ru_stime - total_system_time
            total_system_time = usage.ru_stime
            available_time = debug_timer * cores
            andinopy.andinopy_logger.debug(f"In {debug_timer}s elapsed times:"
                                           f" User-Time: {user_time:06.4f}s"
                                           f", System-Time: {system_time:06.4f}s"
                                           f", Available-Time: {available_time:06.4f}s (elapsed*cores)"
                                           f", %-Time total used: {(user_time + system_time) / available_time:07.4%}"
                                           f", Max Memory Used: {usage.ru_maxrss / 1024}mb"
                                           f", Active threads: {threading.active_count()}")
except SystemExit as ex:
    print("sys exit")

finally:
    # Keyboard interrupt ...
    print("stopped")
    # Stop the server to free the socket in all cases
    server.stop()
