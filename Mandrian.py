__author__ = 'Alan Richmond'
'''
    Mandrian.py     Copyright (C) 2015 Alan Richmond (Tuxar.uk, FractalArt.Gallery)
    ===========     MIT License
    A Python + Pygame program to render the Mandelbrot Set by sub-dividing square areas into sub-squares.
    If the square's corners all have the same iteration count from the escape function we assume there's no internal
    detail to render. We also use the iteration count to select an audio frequency and play a note. Colours are either
    tied to the iteration count, or are random. The squares may be bordered. The effect is a little similar to
    Mondrian's paintings. The program's name is a portmanteau of Mandelbrot and Mondrian.
    If sound>0 the program plays notes, but these slow the program considerably.
    If you want a fast plot, turn off sound (sound=0). Type 'help' at the prompt.
        See FractalArt.Gallery (website).
'''
import pygame, pygame.gfxdraw, pyaudio
from collections import deque
from random import randint
from math import sqrt, sin, pi, log

# Major parameters
side = 2 ** 10   # Must be a power of 2
save=True
maxit =colOff=360

# Visuals
sqrtCol = True
randCol = False
line = 0
bg = pygame.Color(0, 0, 0)
h,s,v=0,0,0
bg.hsva=(h,s,v)

#   Audio
sound = 64          # recommended sample rate
#sound=0            # no sound
loFreq = 130.81  # C3
loFreq = 261.63  # C4
#loFreq = 440.00  # A4
#loFreq=523.25   # C5
hiFreq = 6000
octaves = 4
scale='log'

#   Complex plane
xmin = -2.0
xmax = ymax = 1.0
#xmax = -0.5
#ymax = 0.5
ymin = -ymax
#xd = xmax - xmin
#yd = ymax - ymin

#   User Interface. GUI might be better...

def getParameters():
    global side, colOff, sqrtCol, randCol, line, sound, loFreq, hiFreq, octaves, scale, quit,h,s,v
    while not quit:
        input = raw_input("Enter a command (help, go, quit) or parameter followed by value (t=true) [go]: ").lower()

        if input == 'help':
            print "Enter one of the following, followed on the same line by space and new value:", '\n', \
                "side       -   power to raise 2, for display square =>", int(log(side,2)), '\n', \
                "colOff     -   colour offset (0-359, 360=random) =>", colOff, '\n',\
                "sqrtCol    -   square root selection of colours =>", sqrtCol, '\n', \
                "randCol    -   random selection of colours =>", randCol, '\n', \
                "line       -   line thickness (0 = no lines) =>", line, '\n', \
                "sound      -   # of points to skip between notes (0=no sound) =>", sound, '\n', \
                "loFreq     -   lowest frequency of notes >", loFreq, '\n', \
                "hiFreq     -   highest frequency of notes (if log or sqrt) =>", hiFreq, '\n', \
                "octaves    -   how many octaves (if not log or sqrt) =>", octaves, '\n', \
                "scale      -   logarithmic/square root/linear sound gen =>", scale, '\n', \
                "h/s/v      -   background hue (0-360), saturation or value (0-100) =>",h,s,v,'\n',\
                "go         -   go and do it!", '\n', \
                "quit       -   stop program"
        elif input =='go' or input=='': return
        elif input == 'quit':
            quit = True
        else:
            cmds=input.split(',')
            for cmd in cmds:

                param, value = cmd.split()
                print param,value
                if param == 'side':
                    side = 2 ** int(value)
                elif param == 'sqrtcol':
                    sqrtCol = (value == 'true')
                elif param=='randcol'   :   randCol=(value[0]=='t')
                elif param=='line'      :   line=int(value)
                elif param=='sound'     :   sound=int(value)
                elif param=='lofreq'    :   loFreq=int(value)
                elif param=='hifreq'    :   hiFreq=int(value)
                elif param=='octaves'   :   octaves=int(value)
                elif param=='scale'     :   scale=value
                elif param=='h'         :   h=int(value)
                elif param=='s'         :   s=int(value)
                elif param=='v'         :   v=int(value)
                elif param== 'coloff'   :   colOff=int(value)
                else: print 'Unknown parameter'
            else:
                return

#   Sound
PyAudio = pyaudio.PyAudio
p = PyAudio()
RATE = 16000
stream = p.open(format=p.get_format_from_width(1),channels=1,rate=RATE,output=True)
k = 0
root = 1.059463094359 ** 2  # equal temperament twelfth root of 2
notes = []
notes.append(loFreq)
nnotes = octaves * 6
for i in range(1, nnotes):
    notes.append(notes[i - 1] * root)

#   Play a note if sound is 'on'. Select from 'linear', log or sqrt scales
#   by linear I mean equal temperament which I guess is log...

def playNote(it, l):
    if sound==0: return
    global k
    if k % sound == 0:
        if it >= maxit: it = maxit - 1
        if scale=='log':
            f = log(float(it+1)) * hiFreq / log(maxit) + loFreq
        elif scale=='sqrt':
            f = sqrt(float(it)) * hiFreq / sqrt(maxit) + loFreq
        else:
            i = int(float(it * nnotes / maxit))
            if i == 0: return
            f = notes[i]
        d = sqrt(float(l)) / 22.0
        note = ''.join([chr(int(sin(x * f * pi / RATE) * 127 + 128)) for x in xrange(int(d * RATE))])
        stream.write(note)
    k += 1

#   Select a colour: random, sqrt or linear.
fg = pygame.Color(0, 0, 0, 0)
def col(it):
    if it >= maxit - 1: return bg
    if (randCol):
        it = randint(0, maxit - 1)
    elif (sqrtCol):
        it = int(sqrt(float(it)) * sfm)
    fg.hsva = ((it+colOff)%360, 100, 100, 0)
    return fg

#   The heart of the Mandelbrot algorithm with some optimisations
#   e.g.http://en.wikipedia.org/wiki/Mandelbrot_set#Cardioid_.2F_bulb_checking

def mandel(ix, iy):
    global already

    it = already[ix][iy]    # has this point already been seen?
    if (it > -1): return it
    c = complex(xscale * ix + xmin, -yscale * iy + ymax)
    x = c.real
    y = c.imag
    z = 0 + 0j
    it = 0
    y2 = y * y
    qq = (x - 0.25) ** 2 + y2
    if not (qq * (qq + (x - 0.25)) < y2 / 4.0 or (x + 1.0) ** 2 + y2 < 0.0625):
        # while abs(z) < 2 and it < maxit:
        for it in xrange(maxit):
#            z=z**2     # Try different exponents!
            z *= z      # Faster z^2
            z += c
            if abs(z) > 2: break
        else:
            it = maxit
    else:   # note that these it counts (above & below) need to be different
        it = maxit + 1
    already[ix][iy] = it
    return it

already = []
xscale = yscale = 0
quit = False

#   Main Program
#   ============

def main():
    getParameters() # ask user
    if quit: return
    global already, xscale, yscale, sfm,bg,colOff

    bg.hsva=(h,s,v)
#    if colOff>359:
    colOff=randint(0,360)
    already = [[-1 for y in range(side/2)] for x in range(side*3/2)]

#   A square enclosing the Mandelbrot set
    xscale = (xmax - xmin) / (side*1.5)
    yscale = (ymax - ymin) / side
    sfm = sqrt(float(maxit))
    screen = pygame.display.set_mode((side*3/2, side))

#   Add 3 squares to queue, in a line on top of the real axis
    squares = deque([(0, 0, side / 2), (side / 2, 0, side / 2), (side,0,side/2)])

#   Pop squares off the queue
    while squares:
        ix, iy, l = squares.popleft()
        l2 = l / 2
#       Determine colour
        if l == 1:      # down to 1 pixel
            itav = mandel(ix, iy)
            c = col(itav)

        else:
#           Get iteration counts at 4 corners.
#           Need to also add side mid-points to be safe (TBD)
            it = [mandel(ix, iy),
                  mandel(ix + l - 1, iy),
                  mandel(ix + l - 1, iy + l - 1),
                  mandel(ix, iy + l - 1)]
            di = max(it) - min(it)
            itav = sum(it) / 4
            c = col(itav)

#       Draw square
        yn = side - iy - l
        if (line>0):
#           Clunky way to add borders - just shrink the square exposing colour behind!
            b=l-line
            screen.fill(c, pygame.Rect(ix + 1, iy + 1, b,b))
            screen.fill(c, pygame.Rect(ix + 1, yn + 1, b,b))
        else:
            screen.fill(c, pygame.Rect(ix, iy, l, l))
            screen.fill(c, pygame.Rect(ix, yn, l, l))

        pygame.display.update([(ix, iy, l, l), (ix, yn, l, l)])

#       Subdivide square; midpoints
        ixn = ix + l2
        iyn = iy + l2

#       If squares are more than 1 pixel, and there's a variation of iteration counts
        if l > 1 and di > 0:

#           Add sub-squares to queue
            squares.append((ix, iy, l2))
            squares.append((ixn, iy, l2))
            squares.append((ixn, iyn, l2))
            squares.append((ix, iyn, l2))

#       Music, Maestro!
        playNote(itav, l)

    if save:                    # parameters are encoded into filename
        pars='man-{0}_{1}-{2}_{3}-{4}'.format(colOff,h,s,v,side)
        pygame.image.save(screen, pars+'.jpg')
        print "Saved as "+pars+'.jpg'
#        save=False

#    stream.stop_stream()
#    stream.close()
#    p.terminate()

if __name__ == "__main__":
    import time
    # import cProfile
    #    cProfile.run('main()',sort='time')
    times = []
    while not quit:
        start = time.clock()
        main()
        runtime = time.clock() - start
        times.append(runtime)
        tav = sum(times) / len(times)
        print "This time: ",runtime, "Average Time: ", tav