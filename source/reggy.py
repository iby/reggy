#!/usr/local/bin/python3

import sys

from reggy.cli import Cli

# Customize tracer.
# from reggy.tracer import Tracer
# Tracer.skip = True
# Tracer.quiet = False

exit(Cli().run(sys.argv, sys.stdin, sys.stdout, sys.stderr))
