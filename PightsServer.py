#!/usr/bin/env python3
#Info about LED library and supported GPIO usage: https://pypi.org/project/rpi-ws281x/

import time
import argparse
import requests
import logging
import socketserver
import threading
from http.server import BaseHTTPRequestHandler
from rpi_ws281x import PixelStrip, Color, ws

#Global
lightStrip_Frequency  = 800000  #LED signal frequency in hertz (usually 800khz)
lightStrip_DMA        = 10      #DMA channel to use for generating signal (try 10)
lightStrip_Brightness = 200     #Set to 0 for darkest and 255 for brightest
lightStrip_Invert     = False   #True to invert the signal (when using NPN transistor level shift)
lightStrip_Type      = ws.WS2811_STRIP_GRB

#Roof
lightStrip1           = None
lightStrip1_Count     = 51
lightStrip1_Pin       = 18
lightStrip1_Channel   = 0
lightStrip1_Skip      = [0, 30, 51]

#West / Garage
lightStrip2           = None
lightStrip2_Count     = 135
lightStrip2_Channel   = 1
lightStrip2_Pin       = 19
lightStrip2_Skip      = [19, 48, 87, 88, 89]

#East / Office
lightStrip3           = None
lightStrip3_Count     = 99
lightStrip3_Channel   = 0
lightStrip3_Pin       = 21
lightStrip3_Skip      = [16, 45, 57, 58, 59, 60, 61, 62, 63, 64, 65, 96, 97, 98, 99]

#Setup logging
logging.basicConfig(filename="/home/pi/Pights/PightsServer.log", filemode='a', format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
logging.getLogger("urllib3").setLevel(logging.WARNING)

#Clear first X pixels
def clearFirst(lightStrip, count):
    for i in range(count):
        lightStrip.setPixelColor(i, Color(0, 0, 0))
    lightStrip.show()

#Clear all pixels
def clearAll(lightStrip):
    clearFirst(lightStrip, lightStrip.numPixels())

#Clear defined list of pixels
def clearList(lightStrip, clearList):
    for i in range(len(clearList)):
        lightStrip.setPixelColor(clearList[i], Color(0, 0, 0))
    lightStrip.show()

#Set all pixels to single color
def setColor(lightStrip, color):
    for i in range(lightStrip.numPixels()):
        lightStrip.setPixelColor(i, color)
    lightStrip.show()

#Set red/green pattern
def setRedGreenPattern(lightStrip):
    for i in range(lightStrip.numPixels()):
        if i % 2 == 0:
            lightStrip.setPixelColor(i, Color(255, 0, 0))
        else:
            lightStrip.setPixelColor(i, Color(0, 255, 0))
    #lightStrip.show()

#Set red/clear/green/clear pattern
def setRedGreenSkipPattern(lightStrip):
    for i in range(lightStrip.numPixels()):
        if i % 4 == 0:
            lightStrip.setPixelColor(i, Color(255, 0, 0))
        elif i % 2 == 0:
            lightStrip.setPixelColor(i, Color(0, 255, 0))
        else:
            lightStrip.setPixelColor(i, Color(0, 0, 0))
    lightStrip.show()

#Set multi color pattern
def setMultiColorPattern(lightStrip):
    count = 0
    for i in range(lightStrip.numPixels()):
        if count == 0:
            lightStrip.setPixelColor(i, Color(255, 0, 0))
        elif count == 1:
            lightStrip.setPixelColor(i, Color(0, 255, 0))
        elif count == 2:
            lightStrip.setPixelColor(i, Color(255, 128, 0))
        elif count == 3:
            lightStrip.setPixelColor(i, Color(0, 0, 255))
        else:
            lightStrip.setPixelColor(i, Color(255, 0, 255))
        if count == 4:
            count = 0
        else:
            count = count + 1
    lightStrip.show()

#Set red/white pattern
def setRedWhitePattern(lightStrip):
    for i in range(lightStrip.numPixels()):
        if i % 2 == 0:
            lightStrip.setPixelColor(i, Color(255, 0, 0))
        else:
            lightStrip.setPixelColor(i, Color(255, 255, 255))
    lightStrip.show()

#Set orange pattern
def setOrangePattern(lightStrip):
    setColor(lightStrip, Color(255, 110, 0))
    lightStrip.show()

#Set pink pattern
def setPinkPattern(lightStrip):
    setColor(lightStrip, Color(224, 25, 80))
    lightStrip.show()

#Set white pattern
def setWhitePattern(lightStrip):
    setColor(lightStrip, Color(200, 200, 200))
    lightStrip.show()

#Set pattern for all strips
def setPatternForAll(func):
    func(lightStrip1)
    func(lightStrip2)
    func(lightStrip3)

    clearList(lightStrip1, lightStrip1_Skip)
    clearList(lightStrip2, lightStrip2_Skip)
    clearList(lightStrip3, lightStrip3_Skip)

def setClearForAll():
    clearAll(lightStrip1)
    clearAll(lightStrip2)
    clearAll(lightStrip3)

#Parses and responds to incoming http requests
class GetHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            #Get index for commands that need it
            indexSplit = self.path.split('/')
            index = None
            if len(indexSplit) > 2 and indexSplit[2].isdigit():
                index = int(indexSplit[2])

            if '/SetLightPattern' in self.path and len(indexSplit) > 2:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                if index == 0:
                    setPatternForAll(setRedGreenPattern)
                elif index == 1:
                    setPatternForAll(setRedGreenSkipPattern)
                elif index == 2:
                    setPatternForAll(setMultiColorPattern)
                elif index == 3:
                    setPatternForAll(setRedWhitePattern)
                elif index == 4:
                    setPatternForAll(setWhitePattern)
                elif index == 5:
                    setPatternForAll(setOrangePattern)
                elif index == 6:
                    setPatternForAll(setPinkPattern)
                else:
                    setClearForAll()

                self.wfile.write(bytes('Light pattern ' + str(index) + ' set', 'utf-8'))

            if '/ClearLights' in self.path:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                setClearForAll()
                self.wfile.write(bytes('Lights cleared', 'utf-8'))

        except Exception as e:
            logging.exception("Error processing http request: " + str(e))

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
     pass

try:
    #Create NeoPixel object with appropriate configuration
    lightStrip1 = PixelStrip(lightStrip1_Count, lightStrip1_Pin, lightStrip_Frequency, lightStrip_DMA, lightStrip_Invert, lightStrip_Brightness, lightStrip1_Channel, lightStrip_Type)
    lightStrip2 = PixelStrip(lightStrip2_Count, lightStrip2_Pin, lightStrip_Frequency, lightStrip_DMA, lightStrip_Invert, lightStrip_Brightness, lightStrip2_Channel, lightStrip_Type)
    lightStrip3 = PixelStrip(lightStrip3_Count, lightStrip3_Pin, lightStrip_Frequency, lightStrip_DMA, lightStrip_Invert, lightStrip_Brightness, lightStrip3_Channel, lightStrip_Type)

    #Intialize the library (must be called once before other functions)
    lightStrip1.begin()
    lightStrip2.begin()
    lightStrip3.begin()

    #Setup and start http server
    httpServer = ThreadedTCPServer(("", 80), GetHandler)
    http_server_thread = threading.Thread(target=httpServer.serve_forever)
    http_server_thread.daemon = True
    http_server_thread.start()

    logging.info('Beginning Pights loop')

    while True:
        print("Running...")

        time.sleep(10)

        #Handle all errors so loop does not end
        #except Exception as e:
        #    logging.exception("Error in loop: " + e)

finally:
    #Close down http server and GPIO registrations
    setClearForAll()
    httpServer.shutdown()
    httpServer.server_close()
