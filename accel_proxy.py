import time
from evdev import UInput, ecodes, AbsInfo

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

print("Virtual Accelerometer Created!")
time.sleep(2)

def send_rotation(x, y, z, label):
    """ Send fake accelerometer data with a label """
    ui.write(ecodes.EV_ABS, ecodes.ABS_X, x)
    ui.write(ecodes.EV_ABS, ecodes.ABS_Y, y)
    ui.write(ecodes.EV_ABS, ecodes.ABS_Z, z)
    ui.syn()
    print(f"Sent {label}: X={x}, Y={y}, Z={z}")

try:
    while True:
        print("Testing different orientations...")

        # 1. Default Landscape (Flat, Screen Facing Up)
        #send_rotation(0, 0, 1000, "Landscape (Flat, Facing Up)")
        time.sleep(5)

        # 2. Portrait (Rotated Right)
        send_rotation(1000, 0, 0, "Portrait (Rotated Right)")
        time.sleep(5)

        # 3. Portrait (Rotated Left)
        send_rotation(-1000, 0, 0, "Portrait (Rotated Left)")
        time.sleep(5)

        # 4. Inverted Landscape
        send_rotation(0, 1000, 0, "1k y")
        time.sleep(5)

        # 5. Landscape
        send_rotation(0, -1000, 0, "-1k y")
        time.sleep(5)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    ui.close()
