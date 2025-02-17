import dbus, time, serial, pyudev
from gi.repository import Gio, GLib

MONITOR = 'eDP-1'
DEV_VID = '1b4f' 
DEV_PID = '9204'
CONFIGURED_AXIS = 'y'

# Define states
STATE_LANDSCAPE = "LANDSCAPE"
STATE_LEFT_ROTATION = "LEFT_ROTATION"
STATE_RIGHT_ROTATION = "RIGHT_ROTATION"

# Configurable ranges for detecting orientation
STATE_RANGES = {
    STATE_LANDSCAPE: (-100, 100),         
    STATE_LEFT_ROTATION: (800, float("inf")), 
    STATE_RIGHT_ROTATION: (-float("inf"), -800),  
}

def in_range(value, range_tuple):
    return range_tuple[0] <= value <= range_tuple[1]

def determine_accel_state(accel_data, axis):
    value = accel_data[axis]
    for state, range_config in STATE_RANGES.items():
        if in_range(value, range_config):
            return state
    return None

def dbus_helper(destination = 'org.gnome.Mutter.DisplayConfig',
                path        = '/org/gnome/Mutter/DisplayConfig',
                interface   = 'org.gnome.Mutter.DisplayConfig',
                method      = None,
                args        = None,
                answer_fmt  = None,
                proxy_prpty = Gio.DBusCallFlags.NONE,
                timeout     = -1,
                cancellable = None 
                ):
    
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    reply = bus.call_sync(destination, path, interface,
                      method, args, answer_fmt,
                      proxy_prpty, timeout, cancellable)
    return reply

def unpack_current_state(current_state):
    configuration_serial = current_state[0]
    monitors = current_state[1]
    log_displays = current_state[2]
    logical_displays = []
    for log_display in log_displays:
        logical_display = { 'x_position' : log_display[0],
                            'y_position' : log_display[1],
                            'scale'      : log_display[2],
                            'transform'  : log_display[3],
                            'primary'    : log_display[4]
                          }
        #logical_displays.append(logical_display)
        log_monitors = log_display[5]
        processed_monitors = []
        for monitor in log_monitors:
            processed_monitor = {}
            processed_monitor['connector'] = monitor[0]
            processed_monitor['vendor']    = monitor[1]
            processed_monitor['product']   = monitor[2]
            processed_monitor['serial']    = monitor[3]
            for mon in monitors:
                if mon[0][0] == monitor[0]:
                    processed_monitor['modes'] = mon[1]
            processed_monitors.append(processed_monitor)
        logical_display['monitors'] = processed_monitors
        logical_displays.append(logical_display)
    return configuration_serial, logical_displays

def get_current_state():
    current_state = dbus_helper(method='GetCurrentState', 
                                answer_fmt  = GLib.VariantType.new ('(ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv})')
    )
    
    return unpack_current_state(current_state)
    
def apply_monitors_configuration(configuration_serial, displays, scale):
    displays_arg = []
    
    for display in displays:
        #generate monitors argument for each display
        monitors_arg = []
        display_scale = scale
        for monitor in display['monitors']:
            monitors_arg.append(( 
                        monitor['connector'], 
                        monitor['modes'][0][0], 
                        {
                            'underscanning': GLib.Variant('b', False)
                        }
                    ))
            if scale not in monitor['modes'][0][5]:
                display_scale = 1.0
        display_arg = (
                    display['x_position'], 
                    display['y_position'], 
                    display_scale, 
                    display['transform'], 
                    display['primary'], 
                    monitors_arg, 
                )
        displays_arg.append(display_arg)

    args = GLib.Variant('(uua(iiduba(ssa{sv}))a{sv})', ( configuration_serial, 1,
            displays_arg,
                {
                },
            )
            )
    dbus_helper(method='ApplyMonitorsConfig',
                    args = args)

def get_scale():
    configuration_serial, displays = get_current_state()
    scale = 1.0
    for display in displays:
        if display['scale'] > scale:
            scale = display['scale']
    return scale

def set_scale(scale):
    configuration_serial, displays = get_current_state()
    apply_monitors_configuration(configuration_serial, displays, scale)

def set_rotation(connector, rotation):
    # Map rotation names to transform values
    rotation_map = {
        "normal": 0,
        "left": 1,
        "right": 3,
        "inverted": 6,
    }
    if rotation not in rotation_map:
        raise ValueError(f"Invalid rotation: {rotation}. Must be one of {list(rotation_map.keys())}.")

    # Fetch the current configuration
    configuration_serial, displays = get_current_state()

    # Update the rotation and adjust positions
    updated = False
    rotated_display = None

    for display in displays:
        for monitor in display['monitors']:
            if monitor['connector'] == connector:
                # Store the current width and height
                current_rotation = display['transform']
                current_width = monitor['modes'][0][1] if current_rotation in [0, 6] else monitor['modes'][0][2]
                current_height = monitor['modes'][0][2] if current_rotation in [0, 6] else monitor['modes'][0][1]

                # Update transform and calculate new width and height
                display['transform'] = rotation_map[rotation]
                new_width = monitor['modes'][0][1] if display['transform'] in [0, 6] else monitor['modes'][0][2]
                new_height = monitor['modes'][0][2] if display['transform'] in [0, 6] else monitor['modes'][0][1]

                # Calculate the size difference
                width_diff = new_width - current_width
                height_diff = new_height - current_height

                # Update the rotated display's reference
                rotated_display = {
                    'x_position': display['x_position'],
                    'y_position': display['y_position'],
                    'width_diff': width_diff,
                    'height_diff': height_diff,
                }
                updated = True
                break
        if updated:
            break

    if not updated:
        raise ValueError(f"Display with connector '{connector}' not found.")

    # Adjust neighboring displays
    for display in displays:
        if display['x_position'] > rotated_display['x_position']:
            # Adjust displays to the right
            display['x_position'] += rotated_display['width_diff']
        if display['y_position'] > rotated_display['y_position']:
            # Adjust displays below
            display['y_position'] += rotated_display['height_diff']

    # Apply the updated configuration
    apply_monitors_configuration(configuration_serial, displays, get_scale())
    
def main():
    current_state = None
    previous_state = None

    context = pyudev.Context()
    imu_device = None
    for device in context.list_devices(subsystem='tty'):
        if 'ID_VENDOR_ID' in device and 'ID_MODEL_ID' in device:
            if device.get('ID_VENDOR_ID') == DEV_VID and device.get('ID_MODEL_ID') == DEV_PID:
                print(f"IMU device found at {device.device_node}")
                imu_device = device.device_node

    if not device:
        print("imu device not found")
        return

    

    # Set up the serial connection (adjust port and baud rate as needed)
    ser = serial.Serial(imu_device, 115200, timeout=1)

    print("Monitoring accelerometer data for state transitions")
    print("Monitor:", MONITOR)
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
            # print(f"Accel: X={accel_x}, Y={accel_y}, Z={accel_z}")

            # Determine the current state using the configured axis
            current_state = determine_accel_state(accel_data, CONFIGURED_AXIS)

            # Check for state transition
            if current_state and current_state != previous_state:
                if current_state == STATE_LANDSCAPE:
                    set_rotation(MONITOR, 'normal')
                    print("Landscape")
                elif current_state == STATE_LEFT_ROTATION:
                    set_rotation(MONITOR, 'left')
                    print("Left")
                elif current_state == STATE_RIGHT_ROTATION:
                    set_rotation(MONITOR, 'right')
                    print("Right")
                previous_state = current_state

    except KeyboardInterrupt:
        print("Exiting...")
        ser.close()

if __name__ == "__main__":
    main()
