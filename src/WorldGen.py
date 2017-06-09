from PIL import Image, ImageDraw
from opensimplex import OpenSimplex
import math
import random
import argparse
import threading

#region Argument Parsing

#endregion

class RegionProcessor(threading.Thread):
    def __init__(self, startX, startY, endX, endY, totalWidth, totalHeight, tnoise, mnoise):
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
        super.__init__(self)

    def run(self):
        self.genNoise()
        self.addSlope()
        self.addColor()

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

    def getResult(self):
        return self.world

