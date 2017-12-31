#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import __future__
import subprocess
import sys

dfu = "dfu-util"

dfu_help = '''
The device is probably not in DFU mode
    1. Make sure the USB cable is connected to your desktop (host).
    2. Press the BOOT button on Core Module and keep it pressed.
            BOOT button is on the right side and is marked with letter "B".
    3. Press the RESET button on Core Module while BOOT button is still held.
            RESET button is on the left side and is marked with letter "R".
    4. Release the RESET button.
    5. Release the BOOT button.
'''

dfu_help_install = '''
Please install dfu-util:
sudo apt install dfu-util
Or from https://sourceforge.net/projects/dfu-util/files/?source=navbar
'''


def call(cmd, title, reporthook):
    try:
        proc = subprocess.Popen([dfu] + cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception as identifier:
        raise Exception(dfu_help_install)

    t = 0
    procenta = 0
    out = b""
    while True:
        char = proc.stdout.read(1)
        if not char and proc.poll() is not None:
            break
        if char == b'\t':
            t = 1
            procenta = 0
        elif t:
            if t == 29 and char != b' ':
                procenta = int(char) * 100
            elif t == 30 and char != b' ':
                procenta += int(char) * 10
            elif t == 31:
                procenta += int(char)
            elif t == 32 and char == b'%':
                reporthook(title, procenta, 100)

            t += 1

        if not reporthook:
            sys.stdout.write(out.decode())

        out += char

    if isinstance(out, bytes):
        out = out.decode()

    return out


def flash(filename_bin, reporthook):
    cmd = ["-s", "0x08000000:leave", "-d", "0483:df11", "-a", "0", "-D", filename_bin]

    out = call(cmd, "Flash", reporthook)

    if "No DFU capable USB device available" in out:
        raise Exception(dfu_help)

    if "File downloaded successfully" not in out:
        raise Exception("Error \nlog: \n\n" + out)


def get_list_devices():
    table = []
    try:
        proc = subprocess.Popen([dfu, '--list'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except Exception:
        return table

    while 1:
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        line = line.decode()
        if line.startswith("Found DFU:"):
            serial = line.split()[-1]
            serial = 'dfu:' + serial[serial.find('"') + 1:-1]
            if serial not in table:
                table.append(serial)
    return table

# dfu-util -s 0x08080000 -d 0483:df11 -a 2 -U eeprom.bin