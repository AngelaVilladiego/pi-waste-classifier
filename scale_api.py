import time
import threading
from HX711 import *

REFERENCE_UNIT = -24
ZERO_VALUE = 122930
DATA_PIN = 23
SCK_PIN = 24

hx = None
event_dispatcher = None
last_mass = None
new_mass = None

stop_listening_flag = threading.Event()

def initialize_scale():
    global hx, event_dispatcher, last_mass

    hx = SimpleHX711(DATA_PIN, SCK_PIN, REFERENCE_UNIT, ZERO_VALUE)
    hx.setUnit(Mass.Unit.G)
    hx.zero()
    
    last_mass = hx.weight(20)
    print('Scale initialized')

listen_lock = threading.Lock()
def listen(scale_event_dispatcher):
    with listen_lock:
        
        global event_dispatcher, last_mass, new_mass, hx
        
        stop_listening_flag.clear()
        
        event_dispatcher = scale_event_dispatcher
        
        item_placed_time = None
        item_placed = False
        hx.zero()
        
        try:
            while not stop_listening_flag.is_set():
                new_mass = hx.weight(20)
                current_time = time.time()
                
                mass_difference = new_mass.getValue() - last_mass.getValue()
                
                if stop_listening_flag.is_set():
                    break
                
                if (not item_placed and mass_difference > 4):
                    item_placed = True
                    item_placed_time = current_time
                    event_dispatcher.dispatch('item_placed')
                    
                elif (item_placed and mass_difference < -4):
                    item_placed = False
                    event_dispatcher.dispatch('item_removed')
                    hx.zero()
                
                # Item is placed and settled
                elif item_placed and current_time - item_placed_time >= 1:
                    event_dispatcher.dispatch('item_settled')
                
                last_mass = new_mass
                
        except Exception as e:
            print(f"Error while listening to scale: {e}")
            
        finally:
            print("Exiting scale listening loop.")
            hx.zero()  # Zero the scale on exit

def stop_listening():
    global hx
    stop_listening_flag.set()
    hx.zero()
