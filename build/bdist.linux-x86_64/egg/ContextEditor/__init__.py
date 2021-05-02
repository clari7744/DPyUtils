# -*- coding: utf-8 -*-

"""
ContextEditor
~~~~~~~~~~~~~

A standalone context editor system. This allows the user to edit their message, and the command response will be edited accordingly. Add `bot.load_extension("ContextEditor")` to use this.
:copyright: (c) 2021-present Clari
:license: MIT, see LICENSE for more details.
"""

from context import *


def setup(bot: commands.Bot):
    Editor(bot)
