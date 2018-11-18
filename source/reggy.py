#!/usr/local/bin/python3

from reggy.cli import Cli
import sys

exit(Cli().run(sys.argv, sys.stdin, sys.stdout, sys.stderr))
