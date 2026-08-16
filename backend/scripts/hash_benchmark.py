import hashlib
import os
import time


PAYLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
payload = os.urandom(PAYLOAD_SIZE)

print(f"Benchmark payload: {PAYLOAD_SIZE / (1024 * 1024):.0f} MB")
print()

for algo in ("md5", "sha1", "sha256"):
    start = time.perf_counter()

    hashlib.new(algo, payload).hexdigest()

    elapsed = time.perf_counter() - start

    print(f"{algo:>6}: {elapsed:.4f}s")