def main(filename):
	with open(filename, "r") as f:
		lines = f.readlines()
	cleaned = ""
	for line in lines:
		if not line.startswith("<rect"):
			cleaned += line
	with open(f"flag_{filename}","w") as f:
		f.write(cleaned)

if __name__ == '__main__':
	filename = "invisible.svg"
	main(filename)