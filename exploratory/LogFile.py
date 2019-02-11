from datetime import datetime


# NOTE(tfs; 2019-02-11): This is hard-coded for now. If the date/time format changes, this breaks
#           This is simpler than a regular expression, and the RE doesn't really add much power
#           as it breaks when the format changes too.
TIMESTAMP_LENGTH = 23
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"


class LogFile:

	def __init__(self, filelines):
		"""
			@param filelines Takes a list of file lines (e.g., result of [file].readlines())

			Creates a class that tracks log lines and timestamps
		"""

		self.rawlines = [l.strip() for l in filelines]
		self.timestamps = [LogFile.get_timestamp(l) for l in filelines]
		self.first_timestamp = self.get_first_timestamp()

		if self.first_timestamp is None:
			raise Exception('No valid timestamps found')

		self.timestamp_offsets = self.get_timestamp_offsets()
		self.timestamp_diffs = self.get_timestamp_diffs()


	def get_first_timestamp(self):
		for t in self.timestamps:
			if t is not None:
				return t

		return None


	def get_timestamp_diffs(self):
		diffs = []

		prev = None

		for i in range(len(self.timestamp_offsets)):
			t = self.timestamp_offsets[i]
			if t is None:
				continue

			if prev is None:
				prev = t
			else:
				diffs.append(t - prev)
				prev = t

		return diffs


	def get_timestamp_offsets(self):
		offs = []
		# first = None

		for i in range(len(self.timestamps)):
			t = self.timestamps[i]
			if t is None:
				offs.append(None)
			else:
				offs.append((t - self.first_timestamp).total_seconds())

		return offs


	@staticmethod
	def get_timestamp(rawline):
		""" Returns datetime objects """

		# Ex: "2019-02-08 13:16:00.890"

		timestamp = rawline.strip()[:23]

		if len(timestamp) < 23:
			return None

		try:
			dt = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
			# return int(time.mktime(t))
			return dt
		except:
			return None


