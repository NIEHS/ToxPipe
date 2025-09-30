import subprocess

result = subprocess.run(["fastapi", "run", "../src/toxpipe-api/main.py"], capture_output=True, text=True)
print(f"Output: {result.stdout.strip()}")
print(f"Errors: {result.stderr.strip()}")