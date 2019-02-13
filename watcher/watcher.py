import slack_url # This is to avoid uploading a relatively private piece of information
import requests
import argparse
import sys, os
import time
import psutil

from datetime import datetime

import signal


fallback_dirname = 'unknown'


def signal_handler(sig, frame):
	send_final(fallback_dirname)
	sys.exit(0)


def get_timestamp():
	return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def format_file_list(file_names, file_sizes):
	return "\n".join([format_file_size(file_sizes[i]) + file_names[i] for i in range(len(file_names))])


def format_file_size(num_bytes):
	units = ['B', 'KB', 'MB', 'GB', 'TB']

	unit = 0

	itr = num_bytes

	while unit < 4 and itr > 1024:
		itr /= 1024
		unit += 1

	return str(round(itr, 2)) + ' ' + units[unit]


def gen_file_fields(files):
	fields = []

	for fn in list(files.keys()):
		data = files[fn]

		obj = {}
		obj['title']  = fn
		obj['value']  = "Last Modified: " + data['timestamp'].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "\n"
		obj['value'] += "Size: " + str(format_file_size(data['size']))
		obj['short']  = "false"

		fields.append(obj)

	return fields


def gen_removed_fields(fns):
	fields = []

	for fn in list(fns.keys()):
		data = fns[fn]

		obj = {}
		obj['title']  = fn
		obj['value']  = "Removed"
		obj['short']  = "false"

		fields.append(obj)

	return fields


def gen_new_file_attach(fields):
	return {
		"fallback": "New File(s)",
		"title": "New File(s)",
		"color": "good",
		"fields": fields
	}


def gen_changed_file_attach(fields):
	return {
		"fallback": "Changed File(s)",
		"title": "Changed File(s)",
		"color": "warning",
		"fields": fields
	}


def gen_removed_file_attach(fields):
	return {
		"fallback": "Removed File(s)",
		"title": "Removed File(s)",
		"color": "danger",
		"fields": fields
	}


def send_message(num_changed, dirname, space_remaining, accumulated, total, new_files, changed_files, removed_files):
	new_file_fields = gen_file_fields(new_files)
	changed_file_fields = gen_file_fields(changed_files)
	removed_file_fields = gen_removed_fields(removed_files)

	timestamp = get_timestamp()

	fallback_msg  = str(timestamp) + ": Update watching " + dirname + ".\n"
	fallback_msg += "            " + str(num_changed) + " .tif(f) files added since last poll.\n"
	fallback_msg += "            " + str(accumulated) + " .tif(f) files added since watcher started.\n"
	fallback_msg += "            " + str(total) + " total .tif(f) files in " + dirname + ".\n"
	fallback_msg += "            " + str(round(space_remaining, 2)) + " GB available."

	attachments = [{
		"fallback": fallback_msg,
		"title": "Stats",
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
				"title": "Files Added Since Last Poll",
				"value": str(num_changed),
				"short": "false"
			},
			{
				"title": "Space Available",
				"value": str(round(space_remaining, 2)) + " GB",
				"short": "false"
			},
			{
				"title": "Accumulated Files Since Start",
				"value": str(accumulated),
				"short": "false"
			},
			{
				"title": "Total Files",
				"value": str(total),
				"short": "false"
			}
		]
	}]

	if len(new_file_fields) > 0:
		attachments.append(gen_new_file_attach(new_file_fields))
	if len(changed_file_fields) > 0:
		attachments.append(gen_changed_file_attach(changed_file_fields))
	if len(removed_file_fields) > 0:
		attachments.append(gen_removed_file_attach(removed_file_fields))

	requests.post(slack_url.log_url, json={
		"text": "*" + str(timestamp) + ": Watcher Update*",
		"attachments": attachments
	})


def count_tiffs(watchpath):
	raw = os.listdir(watchpath)

	return len([fn for fn in raw if fn.endswith('.tiff') or fn.endswith('.tif')])


def get_tiff_names(watchpath):
	raw = os.listdir(watchpath)

	tiffs = [fn for fn in raw if fn.endswith('.tiff') or fn.endswith('.tif')]

	obj = {}

	for fn in tiffs:
		obj[fn] = True

	return obj


def get_modified_tiffs(watchpath):
	raw = os.listdir(watchpath)

	tiffs = [fn for fn in raw if fn.endswith('.tiff') or fn.endswith('.tif')]

	mods = [datetime.fromtimestamp(os.path.getmtime(os.path.join(watchpath, fn))) for fn in tiffs]

	obj = {}

	for i in range(len(tiffs)):
		obj[tiffs[i]] = mods[i]

	return obj


def get_changed_files(old_dict, new_dates, last_timestamp):
	removed = {}
	changed = {}
	news = {}

	for fn in old_dict:
		removed[fn] = True

	for fn in new_dates:
		if not fn in old_dict:
			news[fn] = True

		if new_dates[fn] > last_timestamp and not fn in news:
			changed[fn] = True

		if fn in removed:
			del removed[fn]

	return ( news, changed, removed )


def get_stats_fn(watchpath, fname):
	obj = {}
	obj['timestamp'] = datetime.fromtimestamp(os.path.getmtime(os.path.join(watchpath, fname)))
	obj['size'] = os.path.getsize(os.path.join(watchpath, fname))

	return obj


def get_stats_dict(watchpath, file_dict):
	new_obj = {}

	for fn in file_dict.keys():
		new_obj[fn] = get_stats_fn(watchpath, fn)

	return new_obj


def send_initial(dirname, initcount, space):
	timestamp = get_timestamp()

	fallback_msg  = "NOTICE: Started watching " + dirname + ".\n"
	fallback_msg += str(initcount) + " .tif(f) files at start."

	requests.post(slack_url.log_url, json={
		"attachments": [{
			"fallback": fallback_msg,
			"color": "#00FFFF",
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
					"value": str(round(space, 2)) + " GB",
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

	fallback_msg = timestamp + ": Watcher stopped watching directory '" + dirname + "'."

	requests.post(slack_url.log_url, json={
		"attachments": [{
			"fallback": fallback_msg,
			"color": "#0000FF",
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
	free_gigs = psutil.disk_usage(watchpath).free / (1024 * 1024 * 1024)

	return free_gigs


def run(watchpath, interval, duration, space_limit):
	signal.signal(signal.SIGINT, signal_handler)

	init_time = datetime.now()

	# Send startup message
	count = count_tiffs(watchpath)
	init_count = count
	old_files = get_tiff_names(watchpath)

	pathparts = os.path.split(watchpath)

	dirname = watchpath
	fallback_dirname = dirname

	space_remaining = get_avail_space(watchpath)

	send_initial(dirname, count, space_remaining)

	old_timestamp = datetime.now()

	while duration is None or (datetime.now() - init_time).total_seconds() < (duration * 60 * 60):
		time.sleep(interval * 60)

		newcount = count_tiffs(watchpath)

		diff = 0

		space_remaining = get_avail_space(watchpath)

		new_mod_times = get_modified_tiffs(watchpath)

		(news, changed, removed) = get_changed_files(old_files, new_mod_times, old_timestamp)

		if (space_remaining < space_limit):
			send_disk_space_warning(dirname, space_remaining)

		if newcount == count or newcount < count:
			diff = newcount - count
			count = newcount
			send_warning(diff, dirname)
		else:
			diff = newcount - count
			count = newcount

		total = newcount
		accumulated = newcount - init_count

		send_message(diff, dirname, space_remaining, accumulated, total, get_stats_dict(watchpath, news), get_stats_dict(watchpath, changed), removed)

		old_files = get_tiff_names(watchpath)
		old_timestamp = datetime.now()

	send_final(dirname)


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('-w', '--watch', help="ABSOLUTE path to DIRECTORY where .tif(f) files will be saved", required=True)
	parser.add_argument('-i', '--interval', help="Number of MINUTES to wait between polls. Default 21", type=float, default=21)
	parser.add_argument('-d', '--duration', help="Number of HOURS to run the watcher. Default 'None': run until manually closed.", type=float, default=None)
	parser.add_argument('-ls', '--low_space', help="Threshold for sending a low disk space warning, in gigabytes. Default 300.", type=float, default=300)

	opts = parser.parse_args()

	run(opts.watch, opts.interval, opts.duration, opts.low_space)


if __name__ == "__main__":
	main()
