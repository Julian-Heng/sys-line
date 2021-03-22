#!/usr/bin/env python3

from sys_line.core.plugin.wm.abstract import (AbstractWindowManager,
                                              WindowManagerStub)
from sys_line.core.plugin.wm.plugin import Xorg


class WindowManager(WindowManagerStub):

    @staticmethod
    def _post_import_hook(plugin):
        wms = {
            "Xorg": Xorg,
        }

        return super(WindowManager, WindowManager)._detect_window_manager(wms)
