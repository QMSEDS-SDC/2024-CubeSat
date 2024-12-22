#include <iostream>
using namespace std;

extern "C" {
  int main(double input) {
    cout << "The Number Entered Was " << input;
    return 0;
  }
}