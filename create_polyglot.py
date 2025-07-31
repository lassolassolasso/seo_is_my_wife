import subprocess

PGN_FILE = "filtered_960_bots_2200plus.pgn"
BOOK_FILE = "book.bin"
MOVE_COUNT = "40"
PLY_DEPTH = "16"

print(f"📘 Building book from {PGN_FILE}...")

# Build the book builder binary (only if not already built)
subprocess.run(["g++", "book_make.cpp", "-o", "bookbuilder"], check=True)

# Run the binary to generate the book
subprocess.run(["./bookbuilder", PGN_FILE, BOOK_FILE, MOVE_COUNT, PLY_DEPTH], check=True)

print(f"✅ Saved book to {BOOK_FILE}")
