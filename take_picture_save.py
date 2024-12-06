import camera_api as cam

def main(args):
    while True:
        uin = input('press enter to take photo')
        
        if uin == 'exit':
            break
        cam.initialize_camera()
        image_path = cam.take_picture()
        cam.release_camera()
        print(f'photo saved to {image_path}\n')
            
    cam.release_camera()
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
