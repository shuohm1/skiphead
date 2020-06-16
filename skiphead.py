#!/bin/sh
""":" .

exec python3 "$0" "$@"
" """

import argparse
import glob
import os.path
import subprocess
import sys

def main(command="tail", ignore_fd=False, dryrun=False,
         klines=1, kbytes=None, remainder=tuple()):
  args = [command]
  if kbytes is not None:
    args += ["--bytes", f"+{kbytes + 1}"]
  else:
    args += ["--lines", f"+{klines + 1}"]
  args += list(remainder)

  if dryrun:
    print(" ".join(args))
    return 0

  my_stdin = None
  if not sys.stdin.isatty():
    # if stdin is piped
    my_stdin = sys.stdin

  my_fds = tuple()
  if not ignore_fd:
    # check file descriptors
    fdpaths = glob.glob("/proc/self/fd/*")
    my_fds = tuple(int(os.path.basename(path)) for path in fdpaths)

  return subprocess.run(args, stdin=my_stdin, pass_fds=my_fds).returncode

def parse(argv):
  def positive_int(s):
    v = int(s)
    if v <= 0:
      raise argparse.ArgumentTypeError(f"{s} is not a positive integer")
    return v

  parser = argparse.ArgumentParser(allow_abbrev=False,
                                   usage="%(prog)s [options] ...")
  commp = parser.add_argument_group("sub-command arguments")
  metap = parser.add_argument_group("meta arguments")

  commp.add_argument("-n", "--lines", metavar="K", dest="klines",
                     type=positive_int, default=1,
                     help="skip the first K lines (default: %(default)s)")
  commp.add_argument("-c", "--bytes", metavar="K", dest="kbytes",
                     type=positive_int, default=None,
                     help="skip the first K bytes")

  metap.add_argument("--sub-command", metavar="CMD", dest="command",
                     default="tail",
                     help="specify a sub-command instead of \"%(default)s\"")
  metap.add_argument("--ignore-fd", dest="ignore_fd",
                     action="store_true", default=False,
                     help="do not check and pass file descriptors")
  metap.add_argument("--show", "--dryrun", "--dry-run", dest="dryrun",
                     action="store_true", default=False,
                     help="just show arguments without execution")

  return parser.parse_known_args(argv)

if __name__ == "__main__":
  args, remainder = parse(sys.argv[1:])
  sys.exit(main(**vars(args), remainder=remainder))
