#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 
# Copyright 2017 <+YOU OR YOUR COMPANY+>.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import random
import numpy
import pmt

from gnuradio import gr, gr_unittest
from gnuradio import blocks
try:
    import reveng_swig as reveng
except ImportError:
    import reveng

class qa_packet_deframer (gr_unittest.TestCase):

    def setUp (self):
        self.tb = gr.top_block ()
        self.sync = list(map(int, bin(0xd391)[2:].zfill(16)))
        self.plen = list(map(int, bin(4)[2:].zfill(8)))

    def tearDown (self):
        self.tb = None

    def test_001_t (self):
        ''' Test fixed length packet '''
        # set up fg
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        stream = ([0] * 30) + self.sync + data + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, True, len(data), 0, 0, 0, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bits = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        bits = pmt.to_python(pmt.cdr(msg))
        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == data)

    def test_002_t (self):
        '''
        Test variable length packet. Length byte straight after sync, no
        additional bytes.
        '''
        # set up fg
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))

        pkt = self.plen + data
        stream = ([0] * 30) + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 0, 0, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bits = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(meta.get('name') == "boop")

        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == pkt)

    def test_003_t (self):
        '''
        Test variable length packet. Two additional bytes for checksum
        after data packet
        '''
        # set up fg
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = self.plen + data + csum
        stream = ([0] * 30) + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 0, 2, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bits = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == pkt)

    def test_004_t (self):
        '''
        Test variable length packet. Length is indexed two bytes after
        sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + self.plen + data + csum
        stream = ([0] * 30) + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 2, 2, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bits = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bits, numpy.ndarray))
        self.assertTrue(list(bits) == pkt)

    def test_005_t (self):
        '''
        Test two back-to-back variable length packets. Length is indexed one
        byte after sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + self.plen + data + csum
        stream = ([0] * 30) + self.sync + pkt + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 2, 2, False)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        for idx in range(2):
            msg = sink.get_message(0)
            self.assertTrue(pmt.is_pair(msg))
            meta = pmt.to_python(pmt.car(msg))
            bits = pmt.to_python(pmt.cdr(msg))

            self.assertTrue(isinstance(meta, dict))
            self.assertTrue(isinstance(bits, numpy.ndarray))
            self.assertTrue(list(bits) == pkt)

    def test_006_t (self):
        ''' Test fixed length packet '''
        # set up fg
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        stream = ([0] * 30) + self.sync + data + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, True, len(data), 0, 0, 0, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bytez = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0xde, 0xad, 0xbe, 0xef])

    def test_007_t (self):
        '''
        Test variable length packet. Length byte straight after sync, no
        additional bytes.
        '''
        # set up fg
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))

        pkt = self.plen + data
        stream = ([0] * 30) + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 0, 0, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bytez = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(meta.get('name') == "boop")

        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x04, 0xde, 0xad, 0xbe, 0xef])

    def test_008_t (self):
        '''
        Test variable length packet. Two additional bytes for checksum
        after data packet
        '''
        # set up fg
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = self.plen + data + csum
        stream = ([0] * 30) + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 0, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bytez = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

    def test_009_t (self):
        '''
        Test variable length packet. Length is indexed two bytes after
        sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + self.plen + data + csum
        stream = ([0] * 30) + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 2, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        # check data
        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bytez = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x00, 0x01, 0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

    def test_010_t (self):
        '''
        Test two back-to-back variable length packets. Length is indexed one
        byte after sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt = txid + self.plen + data + csum
        stream = ([0] * 30) + self.sync + pkt + self.sync + pkt + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 0, 2, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        for idx in range(2):
            msg = sink.get_message(0)
            self.assertTrue(pmt.is_pair(msg))
            meta = pmt.to_python(pmt.car(msg))
            bytez = pmt.to_python(pmt.cdr(msg))

            self.assertTrue(isinstance(meta, dict))
            self.assertTrue(isinstance(bytez, numpy.ndarray))
            self.assertTrue(list(bytez) == [0x00, 0x01, 0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

    def test_011_t (self):
        '''
        Test that max length drops packet with corrupted length byte. Send
        back-to-back variable length packets. Length is indexed one
        byte after sync. Two additional bytes for checksum after data packet.
        '''
        # set up fg
        txid = list(map(int, bin(0x0001)[2:].zfill(16)))
        p_bad_len = list(map(int, bin(99)[2:].zfill(8)))
        data = list(map(int, bin(0xdeadbeef)[2:].zfill(32)))
        csum = list(map(int, bin(0xa55a)[2:].zfill(16)))

        pkt1 = txid + p_bad_len + data + csum
        pkt2 = txid + self.plen + data + csum

        stream = ([0] * 30) + self.sync + pkt1 + self.sync + pkt2 + ([0] * 30)

        src = blocks.vector_source_b(stream)
        test_blk = reveng.packet_deframer('boop', self.sync, False, 0, 4, 2, 2, True)
        sink = blocks.message_debug()

        self.tb.connect(src, test_blk)
        self.tb.msg_connect(test_blk, 'out', sink, 'store')
        self.tb.run()

        msg = sink.get_message(0)
        self.assertTrue(pmt.is_pair(msg))
        meta = pmt.to_python(pmt.car(msg))
        bytez = pmt.to_python(pmt.cdr(msg))

        self.assertTrue(isinstance(meta, dict))
        self.assertTrue(isinstance(bytez, numpy.ndarray))
        self.assertTrue(list(bytez) == [0x00, 0x01, 0x04, 0xde, 0xad, 0xbe, 0xef, 0xa5, 0x5a])

        try:
            rec_msg = pmt.to_python(sink.get_message(1))
            self.assertTrue(False)
        except RuntimeError:
            pass

if __name__ == '__main__':
    gr_unittest.run(qa_packet_deframer)
