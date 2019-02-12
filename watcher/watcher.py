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


def send_message(num_changed, space_remaining):
	timestamp = get_timestamp()
	spacing = ''.join([' ' for c in timestamp])
	msg  = timestamp + ": " + str(num_changed) + " .tif(f)s have been added since last poll.\n"
	msg += spacing + '  ' + str(round(space_remaining, 2)) + " gigabytes available on the filesystem."
	requests.post(slack_url.log_url, json={'text': msg})


def count_tiffs(watchpath):
	raw = os.listdir(watchpath)

	return len([fn for fn in raw if fn.endswith('.tiff') or fn.endswith('.tif')])


def send_initial(dirname, initcount, space):
	timestamp = get_timestamp()

	fallback_msg  = "NOTICE: Started watching " + dirname + ".\n"
	fallback_msg += str(initcount) + " .tif(f) files at start."

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
					"title": "Initial .tif(f) count",
					"value": str(initcount),
					"short": "false"
				},
				{
					"title": "Space Available",
					"value": str(space) + " GB",
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
			"color": "warn", # Note, this is incorrect. But I like the gray color so I'm leaving it
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


def send_disk_space_warning(dirname, space):
	title = "Low Disk Space"

	fallback_msg = str(round(space, 2)) + " gigabytes remaining."

	timestamp = get_timestamp()

	requests.post(slack_url.warn_url, json={
		"attachments": [{
			"fallback": fallback_msg,
			"color": "warning",
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
				},
				{
					"title": "Space Remaining",
					"value": str(round(space, 2)) + " GB",
					"short": "false"
				}
			]
		}]
	})


def get_avail_space(watchpath):
	stats = os.statvfs(watchpath)

	free_gigs = stats.f_frsize * stats.f_bavail / (1024 * 1024 * 1024)

	return free_gigs


# TODO: Input for run duration
def run(watchpath, interval, duration, space_limit):
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

	space_remaining = get_avail_space(watchpath)

	send_initial(dirname, count, space_remaining)

	# while True:
	# 	r = requests.post(ENDPOINT, json={'text': 'testing'})
	# 	print(r)
	# 	time.sleep(1)

	while duration is None or (datetime.now() - init_time).total_seconds() < (duration * 60 * 60):
		time.sleep(interval * 60)

		newcount = count_tiffs(watchpath)

		diff = 0

		space_remaining = get_avail_space(watchpath)

		if (space_remaining < space_limit):
			send_disk_space_warning(dirname, space_remaining)

		if newcount == count or newcount < count:
			diff = newcount - count
			count = newcount
			send_warning(diff, dirname)
		else:
			diff = newcount - count
			count = newcount

		send_message(diff, space_remaining)

	send_final(dirname)


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('-w', '--watch', help="ABSOLUTE path to DIRECTORY where .tif(f) files will be saved", required=True)
	parser.add_argument('-i', '--interval', help="Number of MINUTES to wait between polls. Default 21", type=float, default=21)
	parser.add_argument('-d', '--duration', help="Number of HOURS to run the watcher. Default 'None': run until manually closed.", type=float, default=None)
	parser.add_argument('-ls', '--low_space', help="Threshold for sending a low disk space warning, in gigabytes", type=float, default=75)

	opts = parser.parse_args()

	run(opts.watch, opts.interval, opts.duration, opts.low_space)


if __name__ == "__main__":
	main()
