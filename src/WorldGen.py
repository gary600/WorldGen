from PIL import Image, ImageDraw,ImageFont
from opensimplex import OpenSimplex
import math
import random
import argparse
import threading
import time

startTime = time.time()

# region Argument Parsing
parser = argparse.ArgumentParser(prog="WorldGen", description="Generates a world.")

parser.add_argument(
    "filename",
    type=str,
    help="File to store the result in"
)
parser.add_argument(
    "--no-label",
    action="store_const",
    default=False,
    const=True,
    dest="label",
    help="Disables the label with the seed"
)
parser.add_argument(
    "-s", "--seed",
    type=int,
    default=random.randint(1, 10000),
    dest="seed",
    help="Sets the seed of the world."
)
parser.add_argument(
    "-t", "--threads",
    type=int,
    default=4,
    dest="threads",
    help="Sets how many threads will be utilized by the generator"
)
args = parser.parse_args()

# endregion

def octaveNoise(noise, x, y, octaves):
    total = noise.noise2d(x, y)
    freq = 1
    amp = 1
    max = 1
    for i in range(octaves):
        freq *= 2
        amp *= 0.5
        max += amp
        total += noise.noise2d(x * freq, y * freq) * amp
    return total/max

class RegionProcessor(threading.Thread):
    def __init__(self, startX, startY, endX, endY, totalWidth, totalHeight, tnoise, mnoise, outputImg):
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.width = endX - startX
        self.height = endY - startY
        self.tnoise = tnoise
        self.mnoise = mnoise
        self.totalWidth = totalWidth
        self.totalHeight = totalHeight
        self.terrain = Image.new("L", (self.width, self.height))
        self.moisture = Image.new("L", (self.width, self.height))
        self.world = Image.new("RGB", (self.width, self.height))
        self.outImg = outputImg
        super().__init__()

    def run(self):
        self.genNoise()
        self.addSlope()
        self.addColor()
        self.outImg.paste(self.world, (self.startX, self.startY))

    def genNoise(self):
        tdraw = ImageDraw.Draw(self.terrain)
        mdraw = ImageDraw.Draw(self.moisture)
        for x in range(self.width):
            for y in range(self.height):
                e = min(max(math.floor(octaveNoise(self.tnoise, (x + self.startX) / 100, (y + self.startY) / 100, 8)*127 + 127), 0), 255)
                m = min(max(math.floor(octaveNoise(self.mnoise, (x + self.startX) / 50, (y + self.startY) / 50, 4)*127 + 127), 0), 255)
                tdraw.point((x, y), e)
                mdraw.point((x, y), m)
        del tdraw, mdraw

    def addSlope(self):
        maxDist = math.sqrt((self.totalWidth / 2)**2 + (self.totalHeight / 2)**2)
        tdraw = ImageDraw.Draw(self.terrain)
        for x in range(self.width):
            for y in range(self.height):
                dist = math.sqrt(((x + self.startX) - self.totalWidth/2)**2 + ((y + self.startY) - self.totalHeight/2)**2)
                tdraw.point((x, y), self.terrain.getpixel((x, y)) - math.floor(dist / maxDist * 200))
        del tdraw

    def addColor(self):
        wdraw = ImageDraw.Draw(self.world)
        for x in range(self.width):
            for y in range(self.height):
                e = self.terrain.getpixel((x, y))
                m = self.moisture.getpixel((x, y))
                # Hot pink to show gaps
                color = (255,182, 193)
                # Ocean
                if e < 47:
                    color = (0, 119, 190)
                # Beach
                elif e < 57:
                    color = (194, 178, 128)
                # Bare rock
                elif e > 180:
                    color = (128, 132, 135)
                # Tundra
                elif e > 190:
                    color = (219, 255, 255)
                else:
                    # Desert
                    if m < 100:
                        color = (194, 178, 128)
                    # Grassland
                    elif m < 130:
                        color = (77, 189, 51)
                    # Forest
                    elif m < 160:
                        color = (34, 139, 34)
                    # Rainforest
                    else:
                        color = (69, 139, 0)
                wdraw.point((x, y), color)
        del wdraw


if __name__ == "__main__":
    # Calculate the dimensions of the chunk for each thread
    x = args.threads
    n = math.ceil(math.sqrt(x))
    while x % n != 0:
        n += 1
    threadDimX = int(n)
    threadDimY = int(x / n)

    if 480 % threadDimX != 0 or 480 % threadDimY != 0:
        print("Error: Thread count not divisible into resolution (480x480)")
        raise SystemExit
    threadSize = (int(480 / threadDimX), int(480 / threadDimY))

    st = time.time()
    # Create generator threads
    tnoise = OpenSimplex(seed=args.seed)
    random.seed(args.seed)
    mnoise = OpenSimplex(seed=random.randint(1, 10000))
    pool = []
    finalImg = Image.new("RGB", (480, 480))
    for x in range(threadDimX):
        for y in range(threadDimY):
            pool.append(RegionProcessor(
                threadSize[0]*x, threadSize[1]*y,
                threadSize[0]*(x+1), threadSize[1]*(y+1),
                480, 480,
                tnoise, mnoise,
                finalImg
            ))
    print(time.time()-st)

    # Start threads
    for thread in pool:
        st = time.time()
        thread.start()
        print(time.time()-st)

    # Wait for threads to finish
    while [x.is_alive() for x in pool].count(True) > 0:
        print("{} thread(s) are done".format([x.is_alive() for x in pool].count(False)), end="\r")
    print()

    # Add label
    if args.label:
        draw = ImageDraw.Draw(finalImg)
        draw.text((10, 10), "Seed: {}".format(args.seed), font=ImageFont.load("arial"))

    # Save image
    with open(args.filename, "wb") as f:
        finalImg.save(f, "PNG")

    print("Done! Took {:0.2f} seconds.".format(time.time() - startTime))