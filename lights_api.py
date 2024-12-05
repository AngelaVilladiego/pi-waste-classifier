from gpiozero import LED
from time import sleep
import threading

# Constants/globals
_red_led = LED(17)
_green_led = LED(18)
_blue_led = LED(22)

stop_behaviour_flag = threading.Event()

def on(color="all"):
    match color:
        case "red":
            _red_led.on()
        case "green":
            _green_led.on()
        case "blue":
            _blue_led.on()   
        case _:
            _red_led.on()
            _green_led.on()
            _blue_led.on()
    
def off(color="all"):
    match color:
        case "red":
            _red_led.off()
        case "green":
            _green_led.off()
        case "blue":
            _blue_led.off()  
        case _:
            _red_led.off()
            _green_led.off()
            _blue_led.off()
            
def flash(count=1, interval=0.5):
    for i in range(count):
        on("all")
        sleep(interval)
        off("all")
        sleep(interval)

def wave(count=1, interval=0.2):
    for i in range(count):
        on("red")
        sleep(interval)
        on("green")
        sleep(interval)
        on("blue")
        sleep(interval)
        off("red")
        sleep(interval)
        off("green")
        sleep(interval)
        off("blue")
        sleep(interval)

BEHAVIOUR_MAP = {
    'flash': flash,
    'wave': wave
}

def start_continuous_behaviour(behaviour="flash"):
    stop_behaviour_flag.clear()
    
    behaviour_function = BEHAVIOUR_MAP.get(behaviour, flash)
        
    while not stop_behaviour_flag.is_set():
        behaviour_function()

def stop_continuous_behaviour():
    stop_behaviour_flag.set()
    off("all")
    

