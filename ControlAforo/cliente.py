import socket
import RPi.GPIO as IO
import time
from time import sleep
from threading import Thread
from queue import Queue

IO.setwarnings(False)
IO.setmode(IO.BCM)
IO.setup(18, IO.IN) #Se establece el pin que servira para la lectura de datos


estado_puerta = False

def socket_thread(conection): #Metodo encargado de informar que la puerta esta abierta
    global estado_puerta
    estado_puerta = True
    puerta = conection.recv(1024)
    puerta = puerta.decode("UTF-8")
    if puerta == 'closed':
        estado_puerta = False
        return False

def lectura(q): #Metodo que se encarga de la lectura de datos para el envio al servidor
    contador = 0 
    while estado_puerta:
        sleep(0.4)
        if IO.input(18) != 1:
            contador = contador + 1
    q.put(contador)
    
host =  "frt.myddns.me" #DNS publica del server
port = 9000 #Puerto de conexion

conection = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #TCP socket
conection.connect((host, port))

q = Queue() #Cola para compartir datos

while 1:
    
    puerta_abierta = conection.recv(1024)
    puerta_abierta = puerta_abierta.decode("UTF-8")

    if(puerta_abierta == 'open'): #Cuando la puerta se abra empieza a contar
        print(puerta_abierta)
        print("puerta abierta, sensores activos")

        estado_puerta = True
       
        
        thread_soc = Thread( target=socket_thread, args=(conection, ) ) #Esta hebra controla el estado de la puerta
        thread_rea = Thread( target=lectura, args=(q, ) ) #Mientras esta hebra se encarga de leer los resultados del sensor

        thread_soc.start()
        thread_rea.start()
        
        
        thread_soc.join()
        thread_rea.join()
        
        contador = q.get() #Devuelve el valor obtenido por la cola, pasada por referencia a la funcion de lectura
        print("puerta cerrada")
        conection.sendall((str(contador)).encode("UTF-8"))
        
    else:
        conection.close() #Si la puerta esta cerrada cierra la conexion
        