import slack_url # This is to avoid uploading a relatively private piece of information
import requests
import argparse
import sys, os
import time

from datetime import datetime

import signal


fallback_dirname = 'unknown'


def signal_handler(sig, frame):
	send_final(fallback_dirname)
	sys.exit(0)


def get_timestamp():
	return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def send_warning(msg):
	timestamp = get_timestamp()


def send_message(num_changed):
	timestamp = get_timestamp()
	msg = timestamp + ": " + str(num_changed) + " .tiffs have been added since last poll."
	requests.post(slack_url.log_url, json={'text': msg})


def count_tiffs(watchpath):
	raw = os.listdir(watchpath)

	return len([fn for fn in raw if fn.endswith('.tiff')])


def send_initial(dirname, initcount):
	timestamp = get_timestamp()

	fallback_msg  = "NOTICE: Started watching " + dirname + ".\n"
	fallback_msg += str(initcount) + " .tiff files at start."

	requests.post(slack_url.log_url, json={
		# "text": "New watcher started",
		"attachments": [{
			"fallback": fallback_msg,
			"color": "good",
			"title": "New Watcher",
			"fields": [
				{
					"title": "Start time",
					"value": timestamp,
					"short": "false"
				},
				{
					"title": "Location",
					"value": dirname,
					"short": "false"
				},
				{
					"title": "Initial .tiff count",
					"value": str(initcount),
					"short": "false"
				}
			]
		}]
	})


def send_warning(diff, dirname):
	title = "NO FILES ADDED" if diff == 0 else "FILES REMOVED"

	fallback_msg = title

	timestamp = get_timestamp()

	requests.post(slack_url.warn_url, json={
		"text": "ALERT",
		"attachments": [{
			"fallback": fallback_msg,
			"color": "danger",
			"title": title,
			"fields": [
				{
					"title": "Timestamp",
					"value": timestamp,
					"short": "false"
				},
				{
					"title": "Location",
					"value": dirname,
					"short": "false"
				}
			]
		}]
	})


def send_final(dirname):
	timestamp = get_timestamp()

	# requests.post(slack_url.log_url, json={
	# 	"text":	timestamp + ": Watcher stopped watching directory '" + dirname + "'."
	# })

	fallback_msg = timestamp + ": Watcher stopped watching directory '" + dirname + "'."

	requests.post(slack_url.log_url, json={
		# "text": "Watcher Stopped",
		"attachments": [{
			"fallback": fallback_msg,
			"color": "warn",
			"title": "Watcher stopped",
			"fields": [
				{
					"title": "Timestamp",
					"value": timestamp,
					"short": "false"
				},
				{
					"title": "Location",
					"value": dirname,
					"short": "false"
				}
			]
		}]
	})


# TODO: Input for run duration
def run(watchpath, interval, duration):
	signal.signal(signal.SIGINT, signal_handler)

	init_time = datetime.now()

	# Send startup message
	count = count_tiffs(watchpath)

	pathparts = os.path.split(watchpath)

	# Assuming there's at least one real part in the path. Really should be true.
	# dirname = pathparts[-1] if len(pathparts[-1]) > 0 else pathparts[-2]

	# Probably more useful to have the full/absolute path here (whatever was passed in)
	dirname = watchpath
	fallback_dirname = dirname

	# init_message  = "NOTICE: Started watching " + dirname + ".\n"
	# init_message += str(count) + " .tiff files at start."

	send_initial(dirname, count)

	# while True:
	# 	r = requests.post(ENDPOINT, json={'text': 'testing'})
	# 	print(r)
	# 	time.sleep(1)

	while duration is None or (datetime.now() - init_time).total_seconds() < (duration * 60 * 60):
		time.sleep(interval * 60)

		newcount = count_tiffs(watchpath)

		diff = 0

		if newcount == count or newcount < count:
			diff = newcount - count
			count = newcount
			send_warning(diff, dirname)
		else:
			diff = newcount - count
			count = newcount

		send_message(diff)

	send_final(dirname)


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('-w', '--watch', help="ABSOLUTE path to DIRECTORY where .tiff files will be saved", required=True)
	parser.add_argument('-i', '--interval', help="Number of MINUTES to wait between polls. Default 21", type=float, default=21)
	parser.add_argument('-d', '--duration', help="Number of HOURS to run the watcher. Default 'None': run until manually closed.", type=float, default=None)

	opts = parser.parse_args()

	run(opts.watch, opts.interval, opts.duration)


if __name__ == "__main__":
	main()
