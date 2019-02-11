import argparse
import sys, os


def run(logfilename):
	logfile = open(logfilename)

	


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('-i', '--input', help="FULL path to log file (NIS Elements help menu->open log folder)", required=True)

	opts = parser.parse_args()

	run(opts.input)


if __name__ == "__main__":
	main()
