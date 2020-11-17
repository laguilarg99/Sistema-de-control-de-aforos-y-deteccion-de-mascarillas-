#!/usr/bin/env python

import RPi.GPIO as GPIO
import sys
import socket
import signal
from mfrc522 import SimpleMFRC522
import time
import datetime

GPIO.setmode(GPIO.BOARD)
GPIO.setup(8,GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setwarnings(False)

simulation_time = 7
current_simulation_time = 0

reader = SimpleMFRC522()

rfid_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 9000
rfid_socket.bind(('0.0.0.0', port))
rfid_socket.listen(5)

#Gestión de interrupciones
def handler(signum,frame):
    print("\nPrograma Terminado")
    GPIO.cleanup()
    conection.close()
    exit()

#Simulamos la apertura de puertas con un interruptor en el GPIO
def puertas_abiertas():
    input_state = GPIO.input(8)
    if input_state == 0:
        #print(input_state)
        return False
    else:
        #print(input_state)
        return True

#Simulamos la apertura de puertas usando temporizadores
def puertas_abiertas_sim(start_time):
    if (time.perf_counter() - start_time ) < 7.0:
        return False
    else:
        return True

#Lectura de tarjeta
def read_rfid(rfid_reads):
    id, text = reader.read_no_block()
    time.sleep(0.12)
    if not id:
        return rfid_reads
    else:
        print("Tarjeta detectada id: ",id)
        return rfid_reads + 1

#Funcion del cálculo de personas
def calculo_personas(ir, rfid_reads, personas):
    personas = personas - (ir - rfid_reads) + rfid_reads
    return personas


def main():
    signal.signal(signal.SIGINT, handler)
    rfid_reads = 0
    personas = 0
    estado_puertas = False
    conection, addr = rfid_socket.accept()

    print("Conectado por ", addr)

    while True:
        start_time = time.perf_counter()
        while estado_puertas == False:
            rfid_reads = read_rfid(rfid_reads)
            estado_puertas = puertas_abiertas_sim(start_time)

        print("Puertas Abiertas")
        conection.sendall(('open').encode("UTF-8"))
        estado_puertas = False
        start_time = time.perf_counter()

        while estado_puertas == False:
            rfid_reads = read_rfid(rfid_reads)
            estado_puertas = puertas_abiertas_sim(start_time)

        print("Puertas Cerradas")
        conection.sendall(('closed').encode("UTF-8"))
        contador_ir = conection.recv(1024)
        contador_ir = int(contador_ir.decode("UTF-8"))

        print("IR ha contado ", contador_ir)

        start_time = time.perf_counter()

        while (time.perf_counter()- start_time) < 5:
            rfid_reads = read_rfid(rfid_reads)
        personas = calculo_personas(contador_ir,rfid_reads,personas)

        print("Número de personas en el vagón: ", personas)

if __name__ == "__main__":
    main()