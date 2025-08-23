#include "polyglot.h"
#include <iostream>

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: ./bookbuilder make -pgn input.pgn -bin output.bin\n";
        return 1;
    }
    return book_main(argc, argv);
}
