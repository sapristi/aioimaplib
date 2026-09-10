# -*- coding: utf-8 -*-
"""Regression tests for https://github.com/iroco-co/aioimaplib/issues/118.

Responses holding 1000+ lines in a single TCP chunk exceeded the default
recursion limit because ``IMAP4ClientProtocol._handle_responses`` recursed
once per line, surfacing as ``RecursionError`` ("Fatal error on SSL
protocol") instead of delivering the response.
"""
import asyncio
import sys
import unittest

from aioimaplib.aioimaplib import Command, IMAP4ClientProtocol


class TestLargeResponses(unittest.TestCase):
    def test_many_untagged_lines_in_single_chunk(self):
        protocol = IMAP4ClientProtocol(None)
        command = Command("FETCH", "TAG", loop=asyncio.new_event_loop())
        protocol.pending_async_commands["FETCH"] = command
        count = 500
        chunk = b"".join(
            b"* %d FETCH (UID %d FLAGS (\\Seen))\r\n" % (i, i)
            for i in range(1, count + 1)
        )
        # A low limit keeps the test fast and independent of the
        # interpreter default: the old recursive parser needed one frame
        # per line and blows past it, the iterative one stays shallow.
        previous_limit = sys.getrecursionlimit()
        sys.setrecursionlimit(100)
        try:
            protocol.data_received(chunk)
        finally:
            sys.setrecursionlimit(previous_limit)
        self.assertEqual(len(command.response.lines), count)
