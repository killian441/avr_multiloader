# 'avr_multiloader' #

This package provides a python wrapper class for interacting with avrdude.
It also includes a copy of the 'avrdude.conf' file from the Arduino 1.0.5
IDE. This allows stand-alone flashing of compiled '.hex' files.

## 'avrdude' API ##

The 'avr_mulitloader.avrdude' class implements an API for flashing a '.hex'
file to an AVR device.

### 'avrdude' API Usage ###

    from avr_multiloader import avrdude
    a = avrdude(partno='ATmega328P', programmer_id='arduino', baud_rate='115200',
                port='/dev/ttyUSB0')
    output, error_out = a.testConnection()
    output, error_out = a.flash('test.hex', ['-vv'])
    print(output)
