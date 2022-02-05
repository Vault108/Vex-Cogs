from typing import TYPE_CHECKING, Optional

import discord
from redbot.core.bot import Red

from .chat import humanize_bytes, inline_hum_list
from .meta import format_help, format_info, out_of_date_check
from .meta import rich_markup as no_colour_rich_markup
from .version import __version__
