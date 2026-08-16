from app.storage.local import LocalStorage


# ============================================================
# Configuration
# ============================================================

STORAGE_ROOT = "./storage"

# Replace this with the storage_key of an uploaded document.
STORAGE_KEY = "REPLACE_WITH_STORAGE_KEY"


# ============================================================
# Storage
# ============================================================

storage = LocalStorage(STORAGE_ROOT)


# ============================================================
# Tamper with stored encrypted object
# ============================================================

def main():
    print("Reading encrypted object...")

    data = storage.get(STORAGE_KEY)

    if not data:
        raise RuntimeError(
            "Stored object is empty."
        )

    print(f"Original size: {len(data)} bytes")

    # Convert bytes to mutable bytearray
    tampered = bytearray(data)

    # Flip the first byte
    tampered[0] ^= 0xFF

    # Write corrupted object back
    storage.put(
        STORAGE_KEY,
        bytes(tampered),
        "application/octet-stream",
    )

    print("Document successfully tampered with.")
    print()
    print("Now call:")
    print("GET /documents/{id}/verify")
    print()
    print("Expected status: TAMPERED")


if __name__ == "__main__":
    main()