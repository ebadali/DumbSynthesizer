import pygame
import math
import time
import random
from threading import Thread

import queue

import pyaudio
import sys
import numpy as np
import aubio
from colorsys import hsv_to_rgb

circleQueue = queue.Queue()


p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    print("Device number (%i): %s" % (i, p.get_device_info_by_index(i).get('name')))


# TODO: be nice with stream functions;

buffer_size = 4096 # needed to change this to get undistorted audio
pyaudio_format = pyaudio.paFloat32
n_channels = 1
samplerate = 44100
stream = p.open(format=pyaudio_format,
                channels=n_channels,
                rate=samplerate,
                input=True,
                input_device_index=0, # index of the audio source
                frames_per_buffer=buffer_size)

time.sleep(1)

# setup onset detector
tolerance = 0.8
win_s = 4096 # fft size
hop_s = buffer_size // 2 # hop size
onset = aubio.onset("default", win_s, hop_s, samplerate)



class Circle(object):
    def __init__(self, x, y, color, size):
        self.x = x
        self.y = y
        self.color = color
        self.size = size

    def shrink(self):
        self.size -= 2


circleList = []

def create_background(width, height):
        colors = [(255, 255, 255), (212, 212, 212)]
        background = pygame.Surface((width, height))
        tile_width = 20
        y = 0
        while y < height:
                x = 0
                while x < width:
                        row = y // tile_width
                        col = x // tile_width
                        pygame.draw.rect(
                                background, 
                                colors[(row + col) % 2],
                                pygame.Rect(x, y, tile_width, tile_width))
                        x += tile_width
                y += tile_width
        return background

def is_trying_to_quit(event):

        pressed_keys = pygame.key.get_pressed()
        alt_pressed = pressed_keys[pygame.K_LALT] or pressed_keys[pygame.K_RALT]
        x_button = event.type == pygame.QUIT
        altF4 = alt_pressed and event.type == pygame.KEYDOWN and event.key == pygame.K_F4
        escape = event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        return x_button or altF4 or escape

def runRenderer(someFactor=50, fps=60):
        pygame.init()

        info = pygame.display.Info()
        print(info.current_w)
        width = info.current_w-someFactor
        height = info.current_h-someFactor

        radiusThreshold = max(height,width)
        screen = pygame.display.set_mode((width, height) )
        pygame.display.set_caption('press space to see next demo')
        background = create_background(width, height)

        clock = pygame.time.Clock()

        # Game Loop
        while True:

                for event in pygame.event.get():
                        if is_trying_to_quit(event):
                                return
                        # if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        #         demos = demos[1:]
                screen.blit(background, (0, 0))

                # Fetch number of elements from a queue
                # 
                if not circleQueue.empty():
                    intensity = circleQueue.get()
                    randX = random.randint(1,screen.get_width())
                    randY = random.randint(1,screen.get_height())
                    # default size
                    circleList.append(Circle(randX,randY,random_color(),intensity*100))
                
                for place, circle in enumerate(circleList):
                    if circle.size < 1:
                        circleList.pop(place)
                    else:
                        pygame.draw.circle(screen, circle.color, (circle.x, circle.y), circle.size%radiusThreshold)
                    circle.shrink()

                    # draw[0](screen, the_world_is_a_happy_place,randX,randY)
                    # draw[0](screen, the_world_is_a_happy_place,randX+5,randY+20)                    
                    # draw[0](screen, the_world_is_a_happy_place,random.randint(1,screen.get_width()),random.randint(1,screen.get_height()))

                pygame.display.flip()
                # this 1/60 of sec
                clock.tick(fps)
COLORS = [(139, 0, 0), 
          (0, 100, 0),
          (0, 0, 139)]

def pretty_colours(how_many):
    """uses golden ratio to create pleasant/pretty colours
    returns in rgb form"""
    golden_ratio_conjugate = (1 + math.sqrt(5)) / 2
    hue = random.random()  # use random start value
    final_colours = []
    for tmp in range(how_many):
        hue += golden_ratio_conjugate * (tmp / (5 * random.random()))
        hue = hue % 1
        temp_c = [int(round(x * 256)) for x in hsv_to_rgb(hue, 0.5, 0.95)]
        print(temp_c)
        final_colours.append(tuple(temp_c))
    return final_colours


COLORS = pretty_colours(50)

def random_color():
    
    return random.choice(COLORS)    
    # rgbl=[255,0,0]
    # random.shuffle(rgbl)
    # return tuple(rgbl)
print(type(random_color()))
def get_onsets():
    while True:
        try:
            buffer_size = 2048 # needed to change this to get undistorted audio
            audiobuffer = stream.read(buffer_size, exception_on_overflow=False)
            signal = np.fromstring(audiobuffer, dtype=np.float32)
            print(np.max(signal)*10000)
            # print(np.mean(signal))
            if onset(signal):
                circleQueue.put(int(np.max(signal)*100))

        except KeyboardInterrupt:
            print("*** Ctrl+C pressed, exiting")
            break


def timer_based():
   while True:
        try:
            time.sleep(1)
            circleQueue.put(True)

        except KeyboardInterrupt:
            print("*** Ctrl+C pressed, exiting")
            break

audioThread = Thread(target=get_onsets, args=())
audioThread.daemon = True
audioThread.start()
              

# values = pygame.display.Info()
# print(values)
# Pass Virw factpr and fps
runRenderer(someFactor=100,fps=60)

stream.stop_stream()
stream.close()
pygame.display.quit()

