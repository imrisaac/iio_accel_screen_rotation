#!/bin/bash

rm -rf build/accel-sensor-bridge

mkdir -p build/accel-sensor-bridge/DEBIAN
mkdir -p build/accel-sensor-bridge/usr/local/bin
mkdir -p build/accel-sensor-bridge/lib/systemd/system

cp accel_sensor_bridge.py build/accel-sensor-bridge/usr/local/bin/
cp accel-sensor-bridge.service build/accel-sensor-bridge/lib/systemd/system/
cp control build/accel-sensor-bridge/DEBIAN/
cp postinst build/accel-sensor-bridge/DEBIAN/

dpkg-deb --build build/accel-sensor-bridge