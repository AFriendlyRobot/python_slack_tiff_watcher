import argparse
import signal
import sys
from datetime import datetime
import random

MESSAGES = ['alpha', 'beta', "LET'S PLAY PRETEND", 'help']

ERROR = 'DispatchBrokenToApplication'

def signal_handler(sig, frame):
	print('SIGINT logged, sending errors and shutting down')
	


def run(outfilename):
	outfile = open(outfilename, 'w')

	while True:
		outfile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])
		outfile.write(" *nis* ")
		outfile.write(random.choice(MESSAGES))

		sleep(random.random() * 0.5)

	outfile.close()


def main():
	parser = argparse.ArgumentParser()

	parser.add_arg('-o', '--output', help="Log file path", required=True)

	opts = parser.parse_args()

	run(opts.output)

