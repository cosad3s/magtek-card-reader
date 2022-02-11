#!/usr/bin/python3
"""
Read a MagTek USB HID Swipe Reader in Linux.

Dependencies: pyusb

Needs to be run with sudo

Thanks: 
- Micah Carrick (https://github.com/MicahCarrick/magtek-pyusb/blob/master/magtek-pyusb.py)
- https://gist.github.com/kevinoconnor7/4177986 
"""
import os
import sys
import usb.core
import usb.util
import re

VENDOR_ID = 0x0801
PRODUCT_ID = 0x0001
DATA_SIZE = 337

# Define our Character Map per Reference Manual
# http://www.magtek.com/documentation/public/99875206-17.01.pdf
 
chrMap = {
    4:  'a',
    5:  'b',
    6:  'c',
    7:  'd',
    8:  'e',
    9:  'f',
    10: 'g',
    11: 'h',
    12: 'i',
    13: 'j',
    14: 'k',
    15: 'l',
    16: 'm',
    17: 'n',
    18: 'o',
    19: 'p',
    20: 'q',
    21: 'r',
    22: 's',
    23: 't',
    24: 'u',
    25: 'v',
    26: 'w',
    27: 'x',
    28: 'y',
    29: 'z',
    30: '1',
    31: '2',
    32: '3',
    33: '4',
    34: '5',
    35: '6',
    36: '7',
    37: '8',
    38: '9',
    39: '0',
    40: 'KEY_ENTER',
    41: 'KEY_ESCAPE',
    42: 'KEY_BACKSPACE',
    43: 'KEY_TAB',
    44: ' ',
    45: '-',
    46: '=',
    47: '[',
    48: ']',
    49: '\\',
    51: ';',
    52: '\'',
    53: '`',
    54: ',',
    55: '.',
    56: '/',
    57: 'KEY_CAPSLOCK'
}
 
shiftchrMap = {
    4:  'A',
    5:  'B',
    6:  'C',
    7:  'D',
    8:  'E',
    9:  'F',
    10: 'G',
    11: 'H',
    12: 'I',
    13: 'J',
    14: 'K',
    15: 'L',
    16: 'M',
    17: 'N',
    18: 'O',
    19: 'P',
    20: 'Q',
    21: 'R',
    22: 'S',
    23: 'T',
    24: 'U',
    25: 'V',
    26: 'W',
    27: 'X',
    28: 'Y',
    29: 'Z',
    30: '!',
    31: '@',
    32: '#',
    33: '$',
    34: '%',
    35: '^',
    36: '&',
    37: '*',
    38: '(',
    39: ')',
    40: 'KEY_ENTER',
    41: 'KEY_ESCAPE',
    42: 'KEY_BACKSPACE',
    43: 'KEY_TAB',
    44: ' ',
    45: '_',
    46: '+',
    47: '{',
    48: '}',
    49: '|',
    51: ':',
    52: '"',
    53: '~',
    54: '<',
    55: '>',
    56: '?',
    57: 'KEY_CAPSLOCK'
}

# ISO-7811, ISO-7813
# Read https://www.magtek.com/content/documentationfiles/d99800004.pdf
TRACK1_SS = '%'
TRACK1_FS = '^'
TRACK2_3_SS = ';'
TRACK2_3_FS = '='
TRACK_ES = '?'

# Needs privileges to interact with USB devices through usb.core
if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

# find the MagTek reader
device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)

if device is None:
    sys.exit("Could not find MagTek USB HID Swipe Reader.")

# make sure the hiddev kernel driver is not active

if device.is_kernel_driver_active(0):
    try:
        device.detach_kernel_driver(0)
    except usb.core.USBError as e:
        sys.exit("Could not detach kernel driver: %s" % str(e))

# set configuration

try:
    device.reset()
    device.set_configuration()
except usb.core.USBError as e:
    sys.exit("Could not set configuration: %s" % str(e))
    
endpoint = device[0][(0,0)][0]

# wait for swipe

data = []
swiped = False
print("Please swipe your card...")

while 1:
    try:
        read = device.read(endpoint.bEndpointAddress, endpoint.wMaxPacketSize)
        data.append(read)
        if not swiped: 
            print("Reading card...")
        swiped = True

    except usb.core.USBError as e:
        #print(e.args)
        if e.args[0] == 110 and swiped:
            print("Reading card finished (%d bytes read)." % len(data))

            # create a list of 8 bit bytes and remove
            # empty bytes
            ndata = []
            for d in data:
                if d.tolist() != [0, 0, 0, 0, 0, 0, 0, 0]:
                    ndata.append(d.tolist())
        
            # parse over our bytes and create string to final return
            sdata = ''
            for n in ndata:
                # handle non shifted letters
                if n[2] in chrMap and n[0] == 0:
                    sdata += chrMap[n[2]]
                # handle shifted letters
                elif n[2] in shiftchrMap and n[0] == 2:
                    sdata += shiftchrMap[n[2]]
            
            print("Read data: %s" % sdata)
            break  

tracks=sdata.split(TRACK_ES)
track1=""
track2=""
track3=""
for t in tracks:
    if (t[0] == TRACK1_SS):
        track1 = t[1:len(t)]
        track1_fields = track1.split(TRACK1_FS)
        print("[TRACK 1] Raw data: %s" % track1)
        print("[TRACK 1] Primary Account No.: %s" % track1_fields[0])
        if (len(track1_fields) > 1):
            print("[TRACK 1] Name: %s" % track1_fields[1])
        if (len(track1_fields) == 3):
            print("[TRACK 1] Additional Data - Expiration date (YYMM): %s" % track1_fields[2][0:4])
            print("[TRACK 1] Additional Data - Service code: %s" % track1_fields[2][4:7])
            print("[TRACK 1] Discretionary Data - PVKI (PIN Verification Key Indicator): %s" % track1_fields[2][7:8])
            print("[TRACK 1] Discretionary Data - PVV or Offset (PIN Verification Value): %s" % track1_fields[2][8:12])
            print("[TRACK 1] Discretionary Data - CVV or CVC (Card Verification Value or Card Validation Code): %s" % track1_fields[2][12:15])
            print("[TRACK 1] Discretionary Data - Misc. data: %s" % track1_fields[2][15:len(track1_fields[2])])
    if (t[0] == TRACK2_3_SS):
        if(len(track2)==0):
            track2 = t[1:len(t)]
            track2_fields = track2.split(TRACK2_3_FS)
            print("[TRACK 2] Raw data: %s" % track2)
            print("[TRACK 2] Primary Account No.: %s" % track2_fields[0])
            if (len(track2_fields) == 2):
                print("[TRACK 2] Additional Data - Expiration date (YYMM): %s" % track2_fields[1][0:4])
                print("[TRACK 2] Additional Data - Service code: %s" % track2_fields[1][4:7])
                print("[TRACK 2] Discretionary Data - PVKI (PIN Verification Key Indicator): %s" % track2_fields[1][7:8])
                print("[TRACK 2] Discretionary Data - PVV or Offset (PIN Verification Value): %s" % track2_fields[1][8:12])
                print("[TRACK 2] Discretionary Data - CVV or CVC (Card Verification Value or Card Validation Code): %s" % track2_fields[1][12:15])
                print("[TRACK 2] Discretionary Data - Misc. data: %s" % track2_fields[1][15:len(track2_fields[1])])
        else:
            track3 = t[1:len(t)]
            track3_fields = track3.split(TRACK2_3_FS)
            # TODO - Track 3 parsing
            print("[TRACK 3] Raw data: %s" % track3)

if (len(track1) == 0):
    print("[TRACK 1] Not found")
if (len(track2) == 0):
    print("[TRACK 2] Not found")
if (len(track3) == 0):
    print("[TRACK 3] Not found")
