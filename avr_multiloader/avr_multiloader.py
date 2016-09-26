"""
Copyright 2016 Mike Killian

This module allows multiple board to be programmed from the same hex file

Inspired by avr_helpers written by Ryan Fobel
"""

import os
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
import logging
import platform
import warnings

from path import Path
from serial_device2 import WriteError, ReadError, SerialDevice, \
    SerialDevices, find_serial_device_ports, find_serial_device_port

logger = logging.getLogger()

class FirmwareError(Exception):
    pass

class avrdude():
    def __init__(self, partno, programmer_id, baud_rate, port=None, 
                 confpath=None):
        self.partno = partno
        self.programmer_id = programmer_id
        self.baud_rate = baud_rate
        self.avrdudePath = None
        self.avrdudeCommand = 'avrdude'
        if port:
            self.port = port
            logger.info('Connecting to port: {}'.format(self.port))
        else:
            try:
                self.port = find_serial_device_port()
                logger.info('Connecting to port: {}'.format(self.port))
            except RuntimeError as err:
                logger.error('RuntimeError: {}'.format(err))
        if confpath is None:
            self.avrconf = Path(os.path.dirname(__file__))
        else:
            self.avrconf = Path(confpath).abspath()

        self.avrconf = self.avrconf/Path('avrdude.conf')

    def setAvrdudePath(self, pathToAvrdude):
        """Manually set path for avrdude.
        """
        self.avrdudePath = pathToAvrdude

    def _executeCommand(self, options):
        if self.avrdudePath is None:
            cmd = ['avrdude']
        else:
            cmd = [str(self.avrdudePath)]

        cmd.extend(options)

        logger.info('Executing: {}'.format(cmd))

        proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, stdin=PIPE)
        outs, errs = proc.communicate()
        if proc.returncode:
            logger.error('Error executing command: {}'.format(errs))
        return outs,errs

    def flashFirmware(self, hexFile, extraFlags=None):
        options = ['-c', self.programmer_id, '-b', str(self.baud_rate), 
                   '-p', self.partno, '-P', self.port, '-C', self.avrconf,
                   '-U', 'flash:w:{}:i'.format(hexFile)]
        if extraFlags is not None:
            options.extend(extraFlags)

        outs, errs = self._executeCommand(options)
        return outs, errs

    def testConnection(self, extraFlags=None):
        options = ['-c', self.programmer_id, '-b', str(self.baud_rate),
                   '-p', self.partno, '-P', self.port, '-C', self.avrconf]
        if extraFlags is not None:
            options.extend(extraFlags)

        outs,errs = self._executeCommand(options)
        return outs,errs
