# -*- coding: utf-8 -*-

# For debugging, use this command to start neovim:
#
# NVIM_PYTHON_LOG_FILE=nvim.log NVIM_PYTHON_LOG_LEVEL=INFO nvim
#
#
# Please register source before executing any other code, this allow cm_core to
# read basic information about the source without loading the whole module, and
# modules required by this module
from cm import register_source, getLogger, Base

register_source(name='flow',
                abbreviation='',
                priority=9,
                scopes=['javascript'],
                word_pattern=r'[\w$\-]+',
                cm_refresh_patterns=[r'\.'],)

import json
import subprocess
import os
from os import path
from sys import stdout, platform

logger = getLogger(__name__)

class Source(Base):

    def __init__(self, nvim):
        super(Source, self).__init__(nvim)

        self.flowpath = nvim.eval('get(g:, "flow#flowpath", "flow")')
        from distutils.spawn import find_executable

        localflow = path.join(nvim.eval('getcwd()'), 'node_modules', '.bin', 'flow')

        if find_executable(localflow):
            self.flowpath = localflow
        elif find_executable(self.flowpath):
            self.message('message', "No local flow, falling back to globally defined flow: [%s]" % self.flowpath)
        else:
            self.message('error', "No flow binary found locally or globally. Please check your setup.")

    def cm_refresh(self, info, ctx, *args):

        typed = ctx['typed']
        startcol = ctx['startcol']
        filepath = ctx['filepath']
        lnum = ctx['lnum']
        col = ctx['col']
        typed = ctx['typed']

        if os.access(filepath, os.R_OK):
            args = [self.flowpath, 'autocomplete', '--quiet', '--json', '--pretty', filepath, str(lnum), str(col)]
        else:
            args = [self.flowpath, 'autocomplete', '--quiet', '--json', '--pretty', str(lnum), str(col)]

        logger.debug("args: %s", args)

        src = self.get_src(ctx)
        # lines = self.get_src(ctx).split("\n")
        # lines = lines[0: lnum-1]
        # src = "\n".join(lines) + "\n" + typed + self.autotok

        proc = subprocess.Popen(args=args,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

        result, errs = proc.communicate(src.encode('utf-8'), timeout=30)
        errs = errs.decode()
        if errs:
            logger.error("error: [%s]", errs)
            self.message('warning', errs)

        result = json.loads(result.decode())['result']

        logger.debug("result: %s", result)

        matches = []

        for e in result:
            # {
            #   "name":"toString",
            #   "type":"() => string",
            #   "func_details":{"return_type":"string","params":[]},
            #   "path":"/tmp/flow/flowlib_39ed34f4/core.js",
            #   "line":57,
            #   "endline":57,
            #   "start":5,
            #   "end":22
            # },
            item = {}
            item['word'] = e['name']
            item['menu'] = e['type']

            # TODO: snippet

            matches.append(item)

        self.complete(info["name"], ctx, startcol, matches)

