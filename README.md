# accel-sensor-bridge

## Generate deb
./create_deb.sh

## Install deb
sudo apt install ./build/accel-sensor-bridge.deb 

## depends
python3
python3-serial
python3-pyudev
gnome-shell-extension-manager



# gnome shell extensions

## debug
journalctl /usr/bin/gnome-shell -f