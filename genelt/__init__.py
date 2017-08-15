# -*- coding: utf-8 -*-
#
# This file is part of the GeneA project
#
#
#
# Distributed under the terms of the GPL license.
# See LICENSE.txt for more info.

"""Generic Element

SKA Generic Element
"""

from . import release
from . import GeneA
from . import GeneAchild
from . import GeneB
from . import GeneBchild
from . import GeneMaster
from . import GeneTelState
from . import GeneAlarms
from . import GeneSubarray
from . import GeneCapCorrelator
from . import GeneCapPssBeams
from . import GeneCapPstBeams
from . import GeneCapVlbiBeams
from . import FileLogger

from . import Rack
from . import Server
from . import Switch
from . import PDU


__version__ = release.version
__version_info__ = release.version_info
__author__ = release.author