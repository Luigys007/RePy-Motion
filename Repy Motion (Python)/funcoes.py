import sys
import glob
import serial
import serial.tools.list_ports;

def serial_ports():
    ports = serial.tools.list_ports.comports()
    portas=[]
    for port, desc, hwid in sorted(ports):
        portas.append(port)
    return portas
