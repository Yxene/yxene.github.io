import requests

BASE_URL = "http://127.0.0.1:5000" # UPDATE THIS

def main():
	url = f"{BASE_URL}/begin"
	flag = [""] * 42
	while True:
		response = requests.get(url, allow_redirects=False)
		if "/begin" not in url:
			body = response.json()
			for key, value in body.items():
				flag[int(key)] = value

		location = response.headers["Location"]
		if location == "/":
			break
		url = f"{BASE_URL}{location}"
	print(f"polycyber{{{''.join(flag)}}}")


if __name__ == '__main__':
	main()
