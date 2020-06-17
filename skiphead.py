#!/bin/sh
""":" .

exec python3 "$0" "$@"
" """

import argparse
import glob
import os.path
import subprocess
import sys

DEFKLINES = 1
DEFCOMMAND = "tail"

def main(command=DEFCOMMAND, ignore_fds=False, just_show=False,
         klines=DEFKLINES, kbytes=None, remainder=tuple()):
  args = [command]
  if kbytes is not None:
    args += ["--bytes", f"+{kbytes + 1}"]
  else:
    args += ["--lines", f"+{klines + 1}"]
  args += list(remainder)

  if just_show:
    print(" ".join(args))
    return 0

  my_stdin = None
  if not sys.stdin.isatty():
    # if stdin is piped
    my_stdin = sys.stdin

  my_fds = tuple()
  if not ignore_fds:
    # check file descriptors
    fdpaths = glob.glob("/proc/self/fd/*")
    my_fds = tuple(int(os.path.basename(path)) for path in fdpaths)

  return subprocess.run(args, stdin=my_stdin, pass_fds=my_fds).returncode

def parse_argv():
  # TODO: support a value with a plus sign (?)
  def positive_int(s):
    v = int(s)
    if v <= 0:
      raise argparse.ArgumentTypeError(f"not a positive integer: {s}")
    return v

  parser = argparse.ArgumentParser(allow_abbrev=False,
                                   usage="%(prog)s [options] ...")
  skip_opts = parser.add_argument_group("skip options")
  meta_opts = parser.add_argument_group("meta options")

  skip_opts.add_argument("-n", "--lines", metavar="K", dest="klines",
                         type=positive_int, default=DEFKLINES,
                         help="skip the first K lines (default: %(default)s)")
  skip_opts.add_argument("-c", "--bytes", metavar="K", dest="kbytes",
                         type=positive_int, default=None,
                         help="skip the first K bytes")

  meta_opts.add_argument("--command", metavar="CMD", dest="command",
                         default=DEFCOMMAND,
                         help="specify a command instead of \"%(default)s\"")
  meta_opts.add_argument("--ignore-fds", dest="ignore_fds",
                         action="store_true", default=False,
                         help="do not check and pass file descriptors")
  meta_opts.add_argument("--show", dest="just_show",
                         action="store_true", default=False,
                         help="just show arguments without execution")

  args, temp = parser.parse_known_args()

  # check for -nK/-cK
  remainder = []
  for rem in temp:
    if rem.startswith("-n") and rem[2:].isdecimal():
      new_klines = positive_int(rem[2:])
      if args.klines != DEFKLINES:
        msg = (f"{parser.prog}: warning: "
               f"-n/--lines={args.klines} is overwritten "
               f"by -n/--lines={new_klines}")
        print(msg, file=sys.stderr)
      args.klines = new_klines
    elif rem.startswith("-c") and rem[2:].isdecimal():
      new_kbytes = positive_int(rem[2:])
      if args.kbytes is not None:
        msg = (f"{parser.prog}: warning: "
               f"-c/--bytes={args.kbytes} is overwritten "
               f"by -c/--bytes={new_kbytes}")
        print(msg, file=sys.stderr)
      args.kbytes = new_kbytes
    else:
      if rem.startswith("-n") or rem.startswith("-c"):
        # -n[^0-9]+ or -c[^0-9]+
        msg = (f"{parser.prog}: warning: "
               f"unrecognized short option: {rem}, "
               f"it is passed to \"{args.command}\" as it is")
        print(msg, file=sys.stderr)
      remainder.append(rem)

  args.remainder = tuple(remainder)
  return args

if __name__ == "__main__":
  try:
    sys.exit(main(**vars(parse_argv())))
  except KeyboardInterrupt:
    print(file=sys.stderr)
    sys.exit(1)
