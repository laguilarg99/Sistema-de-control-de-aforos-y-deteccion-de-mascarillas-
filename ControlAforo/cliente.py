import socket
import RPi.GPIO as IO
import time
from time import sleep
from threading import Thread
from queue import Queue

IO.setwarnings(False)
IO.setmode(IO.BCM)
IO.setup(18, IO.IN)


estado_puerta = False

def socket_thread(conection):
    global estado_puerta
    estado_puerta = True
    puerta = conection.recv(1024)
    puerta = puerta.decode("UTF-8")
    if puerta == 'closed':
        estado_puerta = False
        return False

def lectura(q): 
    contador = 0 
    while estado_puerta:
        sleep(0.4)
        if IO.input(18) != 1:
            contador = contador + 1
    q.put(contador)
    
host =  "frt.myddns.me" 
port = 9000

conection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conection.connect((host, port))

q = Queue()

while 1:
    
    puerta_abierta = conection.recv(1024)
    puerta_abierta = puerta_abierta.decode("UTF-8")

    if(puerta_abierta == 'open'):
        print(puerta_abierta)
        print("puerta abierta, sensores activos")

        estado_puerta = True
       
        
        thread_soc = Thread( target=socket_thread, args=(conection, ) )
        thread_rea = Thread( target=lectura, args=(q, ) )

        thread_soc.start()
        thread_rea.start()
        
        
        thread_soc.join()
        thread_rea.join()
        
        contador = q.get()
        print("puerta cerrada")
        conection.sendall((str(contador)).encode("UTF-8"))
        
    else:
        conection.close()
        