from PIL import Image, ImageDraw
from opensimplex import OpenSimplex
import math
import random
import argparse
import threading

#region Argument Parsing

#endregion

class RegionProcessor:
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

    def __call__(self):
        self.genNoise()
        self.addSlope()
        self.addColor()

    def genNoise(self):
        tdraw = ImageDraw.Draw(self.terain)
        mdraw = ImageDraw.Draw(self.moisture)
        for x in range(self.width):
            for y in range(self.height):
                tdraw.point((x, y), self.tnoise.noise2d(x + self.startX, y + self.startY))
                mdraw.point((x, y), self.mnoise.noise2d(x + self.startX, y + self.startY))
        del tdraw, mdraw

    def addSlope(self):
        maxDist = math.sqrt((self.totalWidth / 2)**2 + (self.totalHeight / 2)**2)
        tdraw = ImageDraw.Draw(self.terain)
        for x in range(self.width):
            for y in range(self.height):
                pass
                # tdraw.point((x, y), )