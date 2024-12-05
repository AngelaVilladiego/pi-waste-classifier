import cv2
import os

# Globals and constants
IMAGE_DIR = '/home/pi/Garbage_Classifier/images'
next_image_number = None
_cam = None

if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)
   
def set_next_image_number():
    global next_image_number
    
    print('Initializing image file numbering...')
    
    existing_files = os.listdir(IMAGE_DIR)
    
    if not existing_files:
        next_image_number = 1
        return
        
    most_recent_file = max(existing_files, key=lambda f: os.path.getmtime(os.path.join(IMAGE_DIR, f)))
    
    number_str = most_recent_file[9:12] # Getting the number from pi_image_001.jpg format
    next_image_number = int(number_str) + 1
    
    print(f'File numbering initialized. Next number is {next_image_number}')
    
def initialize_camera():
    global _cam
    
    if not next_image_number:
        set_next_image_number()

    _cam = cv2.VideoCapture('/dev/video0')
    
    if not _cam.isOpened():
        print('Error: couldn\'t load camera.')
        exit()
    
    print('Camera initialized')

def take_picture():
    global _cam
    
    if _cam is None:
        print('Camera not initialized. Initializing...')
        initialize_camera()
        
    print('Taking photo...')
    
    ret,image = _cam.read()
    image_path = (os.path.join(IMAGE_DIR, f'pi_image_{next_image_number:03}.jpg'))
    cv2.imwrite(image_path, image)
    
    print(f'Image saved at {image_path}.')
    
    return image_path
    
def release_camera():
    global _cam

    print('Releasing camera.')
    _cam.release()
