#include <Arduino.h>
// define the led pin:
int ledPin = 2;

// put function declarations here:
int myFunction(int, int);

void setup() {
  // put your setup code here, to run once:
  // setup the ledpin as an output:
  pinMode(ledPin, OUTPUT);
  int result = myFunction(2, 3);
}

void loop() {
  // put your main code here, to run repeatedly:
  // turn the led on:
  digitalWrite(ledPin, HIGH);
  delay(1000); // wait for a second
  // turn the led off:
  digitalWrite(ledPin, LOW);
  delay(1000); // wait for a second

}

// put function definitions here:
int myFunction(int x, int y) {
  return x + y;
}