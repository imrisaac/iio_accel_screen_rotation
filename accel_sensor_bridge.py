#!/usr/bin/env python3

import time, dbus, serial, pyudev
from evdev import UInput, ecodes, AbsInfo

IMU_VID = '1b4f'
IMU_PID = '9204'
CONFIGURED_AXIS = 'y'

# Defining IMU rotation states
IMU_ROTATION_STATE_LANDSCAPE = (-100, 100)
IMU_ROTATION_STATE_LEFT_ROTATION = (800, float("inf"))
IMU_ROTATION_STATE_RIGHT_ROTATION = (-float("inf"), -800)


# Defing Display states
DISPLAY_ROTATION_STATE_PORTRAIT_RIGHT = (1000, 0, 0)
DISPLAY_ROTATION_STATE_PORTRAIT_LEFT = (-1000, 0, 0)
DISPLAY_ROTATION_STATE_LANDSCAPE = (0, -1000, 0)
DISPLAY_ROTATION_STATE_LANDSCAPE_INVERTED = (0, 1000, 0)


# Define accelerometer event types
capabilities = {
    ecodes.EV_ABS: [
        (ecodes.ABS_X, AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=1)),
        (ecodes.ABS_Y, AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=1)),
        (ecodes.ABS_Z, AbsInfo(value=0, min=-32768, max=32767, fuzz=0, flat=0, resolution=1)),
    ]
}

# Create a virtual input device
ui = UInput(capabilities, name="Virtual Accelerometer", version=0x3)

def check_rotation_state(accel_x, accel_y, accel_z):
    # Calculate rotation or orientation state based on your criteria
    # Example: you can use accel_x, accel_y, or accel_z to determine the state

    if IMU_ROTATION_STATE_LANDSCAPE[0] <= accel_x <= IMU_ROTATION_STATE_LANDSCAPE[1]:
        return "Landscape"
    elif IMU_ROTATION_STATE_LEFT_ROTATION[0] <= accel_x <= IMU_ROTATION_STATE_LEFT_ROTATION[1]:
        return "Left Rotation"
    elif IMU_ROTATION_STATE_RIGHT_ROTATION[0] <= accel_x <= IMU_ROTATION_STATE_RIGHT_ROTATION[1]:
        return "Right Rotation"
    else:
        return "Unknown State"


def send_rotation(x, y, z):
    ui.write(ecodes.EV_ABS, ecodes.ABS_X, x)
    ui.write(ecodes.EV_ABS, ecodes.ABS_Y, y)
    ui.write(ecodes.EV_ABS, ecodes.ABS_Z, z)
    ui.syn()
    print(f"Sent X={x}, Y={y}, Z={z}")

def main():
    context = pyudev.Context()
    imu_device = None

    # search for our imu device
    for device in context.list_devices(subsystem='tty'):
        if 'ID_VENDOR_ID' in device and 'ID_MODEL_ID' in device:
            if device.get('ID_VENDOR_ID') == IMU_VID and device.get('ID_MODEL_ID') == IMU_PID:
                print(f"IMU device found at {device.device_node}")
                imu_device = device.device_node

    if not imu_device:
        print("IMU device not found")
        return


    if not ui:
        print("Failed to create virtual accelerometer")
        return

    print("Virtual Accelerometer Created")
    time.sleep(1)

    # Set up the serial connection
    ser = serial.Serial(imu_device, 115200, timeout=1)
    print("Monitoring accelerometer data for state transitions")
    print("Configured axis:", CONFIGURED_AXIS)


    try:
        while True:
            # Read accelerometer data from the serial port
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue

            # Parse accelerometer data
            accel_x, accel_y, accel_z = map(float, line.split(","))
            accel_data = {'x': accel_x, 'y': accel_y, 'z': accel_z}
            print(f"Accel: X={accel_x}, Y={accel_y}, Z={accel_z}")


            rotation_state = check_rotation_state(accel_x, accel_y, accel_z)
            print("IMU Rotation State:", rotation_state)

            if rotation_state == "Landscape":
                send_rotation(*DISPLAY_ROTATION_STATE_LANDSCAPE)
            elif rotation_state == "Left Rotation":
                send_rotation(*DISPLAY_ROTATION_STATE_PORTRAIT_LEFT)
            elif rotation_state == "Right Rotation":
                send_rotation(*DISPLAY_ROTATION_STATE_PORTRAIT_RIGHT)
            elif rotation_state ==  "Landscape Inverted":
                send_rotation(*DISPLAY_ROTATION_STATE_LANDSCAPE_INVERTED)
            else:
                print("Unknown State")


    except KeyboardInterrupt:
        print("Exiting...")
        ser.close()
        ui.close()

if __name__ == "__main__":
    main()