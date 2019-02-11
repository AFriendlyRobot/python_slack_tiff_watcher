import argparse
import sys, os

from LogFile import LogFile


def max_diff(log):
	diffs = []
	prev = None

	for i in range(len(log.timestamps)):
		t = log.timestamps[i]
		if prev is None:
			prev = t
		elif t is not None:
			diffs.append(t - prev)
			prev = t

	return diffs


def run(filename):
	flines = open(filename).readlines()

	log = LogFile(flines)


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('-i', '--input', help="Log file (path)", required=True)

	opts = parser.parse_args()

	run(opts.input)


if __name__ == "__main__":
	main()
