#include <Wire.h>
#include <SparkFun_LIS2DH12.h>

SPARKFUN_LIS2DH12 accel;  // Create instance

// Define the moving average filter size (larger size for smoother output)
#define FILTER_SIZE 20

// Buffers for X, Y, and Z axis readings
float x_buffer[FILTER_SIZE] = {0};
float y_buffer[FILTER_SIZE] = {0};
float z_buffer[FILTER_SIZE] = {0};

// Indices for circular buffer
int buffer_index = 0;

void setup() {
  Serial.begin(115200);
  Wire.begin();

  if (accel.begin() == false) {
    Serial.println("Accelerometer not detected. Check wiring.");
    while (1);
  }

  // Initialize buffer with first readings to avoid initial spikes
  if (accel.available()) {
    float raw_x = accel.getX();
    float raw_y = accel.getY();
    float raw_z = accel.getZ();
    for (int i = 0; i < FILTER_SIZE; i++) {
      x_buffer[i] = raw_x;
      y_buffer[i] = raw_y;
      z_buffer[i] = raw_z;
    }
  }
}

// Function to compute moving average
float compute_average(float *buffer, int size) {
  float sum = 0;
  for (int i = 0; i < size; i++) {
    sum += buffer[i];
  }
  return sum / size;
}

void loop() {
  if (accel.available()) {
    // Read raw data
    float raw_x = accel.getX();
    float raw_y = accel.getY();
    float raw_z = accel.getZ();

    // Update buffers
    x_buffer[buffer_index] = raw_x;
    y_buffer[buffer_index] = raw_y;
    z_buffer[buffer_index] = raw_z;

    // Compute filtered values
    float filtered_x = compute_average(x_buffer, FILTER_SIZE);
    float filtered_y = compute_average(y_buffer, FILTER_SIZE);
    float filtered_z = compute_average(z_buffer, FILTER_SIZE);

    // Advance the buffer index (circular buffer)
    buffer_index = (buffer_index + 1) % FILTER_SIZE;

    // Print filtered data
    Serial.print("Filtered Accel: ");
    Serial.print(filtered_x, 1);
    Serial.print(" x, ");
    Serial.print(filtered_y, 1);
    Serial.print(" y, ");
    Serial.print(filtered_z, 1);
    Serial.println(" z");

    delay(50); // Adjust for desired sampling rate
  }
}
