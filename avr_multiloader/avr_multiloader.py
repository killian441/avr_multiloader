"""
Copyright 2016 Mike Killian

This module allows multiple board to be programmed from the same hex file

Inspired by avr_helpers written by Ryan Fobel
"""

import os
from subprocess import Popen, PIPE, STDOUT, CalledProcessError
import itertools
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
            logger.debug('Connecting to port: {}'.format(self.port))
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
        self.errorFlag = False

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

        logger.debug('Executing: {}'.format(cmd))

        proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, stdin=PIPE)
        try:
            outs, errs = proc.communicate(timeout=15)
        except TimeoutExpired:
            proc.kill()
            outs, errs = proc.communicate()
        if proc.returncode:
            logger.error('Error executing command: {}'.format(cmd))
            self.errorFlag = True
        return outs

    def flashFirmware(self, hexFile, extraFlags=None):
        options = ['-c', self.programmer_id, '-b', str(self.baud_rate), 
                   '-p', self.partno, '-P', self.port, '-C', self.avrconf,
                   '-U', 'flash:w:{}:i'.format(hexFile)]
        if extraFlags is not None:
            options.extend(extraFlags)

        outs = self._executeCommand(options)
        return outs

    def testConnection(self, extraFlags=None):
        options = ['-c', self.programmer_id, '-b', str(self.baud_rate),
                   '-p', self.partno, '-P', self.port, '-C', self.avrconf]
        if extraFlags is not None:
            options.extend(extraFlags)

        outs = self._executeCommand(options)
        if self.errorFlag:
            logger.error('testConnection failed: ')
            for l in outs.splitlines():
                logger.error(' {}'.format(l))
            return False
        return True

class avr_multiloader():
    '''Here we give this either one set of parameters and assume all ports are
        the same, or we give a list for any of the parameters.
    '''
    def __init__(self, partno, programmer_id, baud_rate, port=None,
                 confpath=None, hexFile=None):
        self.avrdudePath = None
        self.avrdudeCommand = 'avrdude'

        if confpath is None:
            self.avrconf = Path(os.path.dirname(__file__))
        else:
            self.avrconf = Path(confpath).abspath()

        length = 0
        for i in [partno, programmer_id, baud_rate, hexFile]:
            if isinstance(i,list):
                length = len(i) if length < len(i) else length

        if hexFile is None:
            self.hexFile = None
        else:
            self.hexfile = hexFile if isinstance(hexFile,list) else [hexFile]

        if port is None:
            self.port = find_serial_device_ports()
        else:
            self.port = port if isinstance(port,list) else [port]

        if len(self.port) >= length:
            length = len(self.port)
        else:
            logger.error("More parameters specified than available ports"
                         " - truncating parameters")

        self.partno = [partno[x] for x in range(
                        length)] if isinstance(
                        partno,list) else [partno]*length
        self.programmer_id = [programmer_id[x] for x in range(
                        length)] if isinstance(
                        programmer_id,list) else [programmer_id]*length
        self.baud_rate = [baud_rate[x] for x in range(
                        length)] if isinstance(
                        baud_rate,list) else [baud_rate]*length  

        self.avr = list(avrdude(self.partno[y], self.programmer_id[y],
                                self.baud_rate[y], self.port[y],
                                self.avrconf) for y in range(length))

    def flashFirmware(self, hexFile=None, extraFlags=None):
        self.errorFlag = False
        if self.hexFile is not None and hexFile is None:
            fileToFlash = self.hexFile
        elif hexFile is not None:
            if isinstance(hexFile,list):
                fileToFlash = hexFile.extend(itertools.repeat(hexFile[-1],
                                len(hexFile)-len(self.avr)))
            else:
                fileToFlash = [hexFile]*len(self.avr)
        else:
            logger.error('No hexFile specified')
            return 0

        for count,i in enumerate(self.avr):
            outs = i.flashFirmware(fileToFlash[count], extraFlags)
            if self.errorFlag:
                logger.error('flashFirmware failed for iteration {0}, {1}'
                             ' ({2}) on port {3}'.format(count,
                              self.partno[count],self.programmer_id[count],
                              self.port[count]))
            self.errorFlag = False

    def testConnections(self, extraFlags=None):
        for count,i in enumerate(self.avr):
            test = i.testConnection(extraFlags)
            if test is True:
                print('Test passed for port {0}'.format(i.port))
            else:
                logger.error('Test failed for iteration {0}, {1} ({2}) on '
                             'port {3}'.format(count, self.partno[count],
                             self.programmer_id[count], self.port[count]))
