# uncompyle6 version 2.11.5
# Python bytecode 2.7 (62211)
# Decompiled from: Python 2.7.13 (default, Jan 19 2017, 14:48:08)
# [GCC 6.3.0 20170118]
# Embedded file name: /home/tim/workspace/fonttools/Lib/fontTools/ttLib/tables/G__l_o_c.py
# Compiled at: 2015-09-29 18:27:41
from __future__ import print_function, division, absolute_import
from fontTools.misc.py23 import *
from fontTools.misc import sstruct
from fontTools.misc.textTools import safeEval
from itertools import *
from functools import partial
from . import DefaultTable
import array
import struct
import operator
import warnings
from _ast import Num

Gloc_header = '''
    >        # big endian
    version: 16.16F    # Table version
    flags:        H    # bit 0: 1=long format, 0=short format
                       # bit 1: 1=attribute names, 0=no names
    numAttribs:   H    # NUmber of attributes
'''

class table_G__l_o_c(DefaultTable.DefaultTable):
    """
    Support Graphite Gloc tables
    """
    dependencies = ['Glat']

    def __init__(self, tag=None):
        DefaultTable.DefaultTable.__init__(self, tag)
        self.attribIds = None
        self.numAttribs = 0

    def decompile(self, data, ttFont):
        _, data = sstruct.unpack2(Gloc_header, data, self)
        flags = self.flags
        del self.flags
        self.locations = array.array('I' if flags & 1 else 'H')
        self.locations.fromstring(data[:len(data) - self.numAttribs * (flags & 2)])
        self.locations.byteswap()
        self.attribIds = array.array('H')
        if flags & 2:
            self.attribIds.fromstring(data[-self.numAttribs * 2:])
            self.attribIds.byteswap()

    def compile(self, ttFont):
        data = sstruct.pack(Gloc_header, dict(version=1.0, flags=(bool(self.attribIds) << 1) + (self.locations.typecode == 'I'), numAttribs=self.numAttribs))
        self.locations.byteswap()
        data += self.locations.tostring()
        self.locations.byteswap()
        if self.attribIds:
            self.attribIds.byteswap()
            data += self.attribIds.tostring()
            self.attribIds.byteswap()
        return data

    def set(self, locations):
        long_format = max(locations) >= 65536
        self.locations = array.array('I' if long_format else 'H', locations)

    def toXML(self, writer, ttFont):
        writer.simpletag("attributes", number=self.numAttribs)
        writer.newline()

    def fromXML(self, name, attrs, content, ttFont):
        if name == 'attributes':
            self.numAttribs = int(safeEval(attrs['number']))

    def __getitem__(self, index):
        return self.locations[index]

    def __len__(self):
        return len(self.locations)

    def __iter__(self):
        return iter(self.locations)