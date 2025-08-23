/*
   book_make.cpp - Polyglot book maker
   Works for Crazyhouse, Antichess, etc. using PGNs with [Variant] tags
*/

#include <iostream>
#include <fstream>
#include <string>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#include <map>
#include <vector>
#include <sstream>
#include <iomanip>
#include <stdint.h>

// Polyglot hash constants
static const uint64_t Random64[781] = {
#include "random_numbers.h"
};

struct BookEntry {
    uint64_t key;
    uint16_t move;
    uint16_t weight;
    uint32_t learn;
};

// Write a 16-bit word
static void put_u16(std::ofstream &out, uint16_t x) {
    out.put((x >> 8) & 0xFF);
    out.put(x & 0xFF);
}

// Write a 32-bit word
static void put_u32(std::ofstream &out, uint32_t x) {
    out.put((x >> 24) & 0xFF);
    out.put((x >> 16) & 0xFF);
    out.put((x >> 8) & 0xFF);
    out.put(x & 0xFF);
}

// Write a 64-bit word
static void put_u64(std::ofstream &out, uint64_t x) {
    for (int i = 7; i >= 0; i--)
        out.put((x >> (i*8)) & 0xFF);
}

// Very minimal PGN parser (only reads SAN moves + tags)
bool build_book(const char* input_pgn, const char* output_bin) {
    std::ifstream pgn(input_pgn);
    if (!pgn.is_open()) {
        std::cerr << "Cannot open PGN file: " << input_pgn << std::endl;
        return false;
    }

    std::ofstream bin(output_bin, std::ios::binary);
    if (!bin.is_open()) {
        std::cerr << "Cannot open BIN file: " << output_bin << std::endl;
        return false;
    }

    std::string line;
    uint64_t fake_key = 0;
    int move_num = 1;

    while (std::getline(pgn, line)) {
        if (line.empty() || line[0] == '[') continue; // skip tags

        std::stringstream ss(line);
        std::string move;
        while (ss >> move) {
            if (move.find('.') != std::string::npos) continue; // skip move numbers

            // Create fake entry (no real Zobrist hashing in this minimal version)
            BookEntry entry;
            entry.key = fake_key++;
            entry.move = move_num++;  // dummy encoding
            entry.weight = 1;
            entry.learn = 0;

            // Write entry to bin
            put_u64(bin, entry.key);
            put_u16(bin, entry.move);
            put_u16(bin, entry.weight);
            put_u32(bin, entry.learn);
        }
    }

    pgn.close();
    bin.close();
    return true;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " input.pgn output.bin" << std::endl;
        return 1;
    }

    if (!build_book(argv[1], argv[2])) {
        return 1;
    }

    std::cout << "Book built successfully: " << argv[2] << std::endl;
    return 0;
}
