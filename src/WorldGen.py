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
    type=bool,
    default=False,
    const=True,
    dest="label",
    nargs=0,
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

class RegionProcessor(threading.Thread):
    def __init__(self, startX, startY, endX, endY, totalWidth, totalHeight, tnoise, mnoise, output):
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
        self.out = output
        super.__init__(self)

    def run(self):
        self.genNoise()
        self.addSlope()
        self.addColor()
        self.out[(self.startX, self.startY)] = self.world

    def genNoise(self):
        tdraw = ImageDraw.Draw(self.terrain)
        mdraw = ImageDraw.Draw(self.moisture)
        for x in range(self.width):
            for y in range(self.height):
                tdraw.point((x, y), self.tnoise.noise2d(x + self.startX, y + self.startY))
                mdraw.point((x, y), self.mnoise.noise2d(x + self.startX, y + self.startY))
        del tdraw, mdraw

    def addSlope(self):
        maxDist = math.sqrt((self.totalWidth / 2)**2 + (self.totalHeight / 2)**2)
        tdraw = ImageDraw.Draw(self.terrain)
        for x in range(self.width):
            for y in range(self.height):
                dist = math.sqrt(((self.totalWidth - (x + self.startX)) / 2)**2 + (self.totalHeight - (y + self.startY) / 2)**2)
                tdraw.point((x, y), self.terrain.getpixel((x, y)) - ((dist / maxDist) * 127))
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
    threadDimX = n
    threadDimY = x / n

    if 480 % threadDimX != 0 or 480 % threadDimY != 0:
        print("Error: Thread count not divisible into resolution (480x480)")
        raise SystemExit
    threadSize = (480 / threadDimX, 480 / threadDimY)

    # Create generator threads
    tnoise = OpenSimplex(seed=args.seed)
    random.seed(args.seed)
    mnoise = OpenSimplex(seed=random.randint(1, 10000))
    pool = []
    outputs = {}
    for x in range(threadDimX):
        for y in range(threadDimY):
            pool.append(RegionProcessor(
                threadSize[0]*x, threadSize[1]*y,
                threadSize[0]*(x+1)-1, threadSize[1]*(y+1)-1,
                480, 480,
                tnoise, mnoise,
                outputs
            ))

    # Start threads
    for thread in pool:
        thread.start()

    # Wait for threads to finish
    while [x.is_alive() for x in pool].count(True) > 0:
        print("{} thread(s) are done".format([x.is_alive() for x in pool].count(False)), end="\r")
    print()

    # Stitch together final image
    finalImg = Image.new("RGB", (480, 480))
    for pos, img in outputs.items():
        finalImg.paste(img, pos)

    # Add label
    if args.label:
        draw = ImageDraw.Draw(finalImg)
        draw.text((10, 10), "Seed: {}".format(args.seed), font=ImageFont.load("arial"))

    # Save image
    with open(args.filename, "wb") as f:
        finalImg.save(f)

    print("Done! Took {} seconds.".format(time.time() - startTime))