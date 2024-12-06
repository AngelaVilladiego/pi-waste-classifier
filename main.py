import model_api as model
import camera_api as camera
import lights_api as lights
import scale_api as scale
import time
from lights_api import start_continuous_behaviour
import threading
import signal
import sys

# Constants and globals
WASTE_CATEGORY_MAP = {
    'cardboard': 'recycling',
    'compost': 'compost',
    'glass': 'recycling',
    'metal': 'recycling',
    'paper': 'compost',
    'plastic': 'recycling',
    'trash': 'trash'
}

LED_COLOR_MAP = {
    'recycling': 'blue',
    'trash': 'red',
    'compost': 'green'
}
lights_thread = None
scale_thread = None
event_dispatcher = None
processing_complete_event = threading.Event()
shutdown_flag = threading.Event()

def start_lights(behaviour):    
    global lights_thread
    lights_thread = threading.Thread(target=start_continuous_behaviour, args=(behaviour,))
    lights_thread.daemon = True # Daemon thread will exit when the main program exits
    lights_thread.start()

def stop_lights():
    lights.stop_continuous_behaviour()
    if lights_thread is not None and threading.current_thread() is not lights_thread:
        lights_thread.join()

def start_listening_to_scale():
    global scale_thread, event_dispatcher
    
    if shutdown_flag.is_set():
        return
    
    if scale_thread is not None and scale_thread.is_alive():
        return
    
    def scale_listen_wrapper():
        try:
            if not shutdown_flag.is_set():
                scale.listen(event_dispatcher)  # Adjust as necessary
        except Exception as e:
            if not shutdown_flag.is_set():
                print(f"Error in scale listener: {e}")
        finally:
            print("Scale listener stopped.")
        
    scale_thread = threading.Thread(target=scale_listen_wrapper)
    scale_thread.daemon = True # Daemon thread will exit when the main program exits
    scale_thread.start()
    print('Listening to scale...')

def stop_listening_to_scale():
    print('Turning off scale listening...')
    scale.stop_listening()
    if scale_thread is not None and threading.current_thread() is not scale_thread:
        scale_thread.join()

def on_item_placed():
    if shutdown_flag.is_set():
        return
    print('Item placed on scale. Turning on lights.')
    lights.on()

def on_item_settled():
    if shutdown_flag.is_set():
        return
    
    print('Processing...')
    
    stop_listening_to_scale()
    lights.off()
    
    # Indicate that picture will be taken
    start_lights("wave")
    time.sleep(3)
    stop_lights()
    lights.on()
    
    # Take picture
    camera.initialize_camera()
    image_path = camera.take_picture()
    camera.release_camera()
    lights.off()
    
    # Predict image
    predicted_class, probabilities = model.predict_image(image_path)
    
    print("Probabilities:")
    for prob in probabilities:
        print(f'\t{prob}')  
    
    print(f"Predicted class: {predicted_class}")
    
    waste_category = WASTE_CATEGORY_MAP.get(predicted_class)
    
    print(f'Waste belongs in {waste_category}.')
    
    lights.on(color=LED_COLOR_MAP.get(waste_category))
    
    print()
    
    processing_complete_event.set()
    
def on_item_removed():
    if shutdown_flag.is_set():
        return
    print('Item removed from scale. Turning off lights.')
    stop_lights()

class ScaleEventDispatcher:
    def __init__(self):
        self.handlers = {
            'item_placed': on_item_placed,
            'item_settled': on_item_settled,
            'item_removed': on_item_removed
        }
    
    def dispatch(self, event):
        if shutdown_flag.is_set():
            return
        if event in self.handlers:
            self.handlers[event]()
        else:
            print(f'Unknown event: {event}')

def init():
    global event_dispatcher
    
    model.load_model(filepath="garbage_classification_model.pt", classes_file="classes.pkl")
    # camera.initialize_camera()
    scale.initialize_scale()
    event_dispatcher = ScaleEventDispatcher()

def shutdown_program():
    print('Shutting down...')
    
    # Stop threads
    stop_listening_to_scale()
    stop_lights()
    
    # Release resources
    camera.release_camera()
    lights.off()
    
    print('Shutdown complete.')

def signal_handler(sig, frame):
    print('\nInterrupt signal received. Shutting down...')
    stop_listening_to_scale()
    shutdown_flag.set() # Notify threads to stop

        
    # Wait briefly to allow threads to finish
    time.sleep(0.5)
    
    print('Exiting program.')
    sys.exit(0)

def main(args):
    
    try:
        # Indicate initializing state with flashing lights
        start_lights("wave") 
        init()
        stop_lights()
        
        # Indicate ready state with solid lights
        lights.on() 
        print('\nReady to start.')
        
        while not shutdown_flag.is_set():
            input('Please remove any items from the scale and press Enter to start a new waste classification.')
            lights.off()
        
            # Start event loop listening
            print('Starting waste classification.')
            start_listening_to_scale()
            
            processing_complete_event.wait()
            
            print('Waste classification complete.')
            processing_complete_event.clear()
    
    except KeyboardInterrupt:
        print('Shutdown requested.')
        
    finally:
        shutdown_program()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler) # Handle CTRL+C
    signal.signal(signal.SIGTERM, signal_handler) # Handle termination
    import sys
    sys.exit(main(sys.argv))
