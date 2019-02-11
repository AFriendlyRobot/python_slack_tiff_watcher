from slack_url import url as ENDPOINT
import requests
import time


def main():
	while True:
		r = requests.post(ENDPOINT, json={'text': 'testing'})
		print(r)
		time.sleep(1)


if __name__ == "__main__":
	main()