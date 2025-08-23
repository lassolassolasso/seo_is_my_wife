// book_make.cpp
// Minimal Polyglot Book Builder for Crazyhouse/Antichess/etc.

#include <iostream>
#include <fstream>
#include <string>
#include "polyglot.h"

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " input.pgn output.bin" << std::endl;
        return 1;
    }

    const char* input_pgn = argv[1];
    const char* output_bin = argv[2];

    if (!book_make(input_pgn, output_bin)) {
        std::cerr << "Error: failed to build book." << std::endl;
        return 1;
    }

    std::cout << "Book built successfully: " << output_bin << std::endl;
    return 0;
}
