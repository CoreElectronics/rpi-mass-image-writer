import time
import shlex
import os
import subprocess
from os import listdir
from os.path import isfile, join
from subprocess import Popen, PIPE
from Adafruit_CharLCDPlate import Adafruit_CharLCDPlate

lcd = Adafruit_CharLCDPlate()

nowWriting = False

lcd.clear()

imagePath = "images/"

imageNames = []

currentImageSelection = 0
listOfDrives = []

writeStatusLine = ""

def getConnectedDrives():
    commandOutput = runCommandAndGetStdout("lsblk -d | awk -F: '{print $1}' | awk '{print $1}'")
    splitted = commandOutput.splitlines()

    drives = []

    for drive in splitted:
        if drive != "NAME" and not drive.startswith("mmc"):
            drives.append(drive)
            

    return drives

def powerOff():
    lcd.clear()
    lcd.message("Shutting down...")
    runCommandAndGetStdout("poweroff")



def refreshSystem():
    global imageNames
    global listOfDrives

    filesfound = [ f for f in listdir(imagePath) if isfile(join(imagePath,f)) ]

    imageNames = []
    for file in filesfound:
        if file != ".gitignore":
            imageNames.append(file)


    currentImageSelection = 0;
    listOfDrives = getConnectedDrives()


def refreshLcd():
    numDrives = len(listOfDrives)
    numImages = len(imageNames)

    imageMessage = ""

    if numImages == 0:
        imageMessage = "No images found"
    else:
        imageMessage = imageNames[currentImageSelection]

    lcd.clear()

    driveMessage = ""

    if nowWriting:
        driveMessage = writeStatusLine + "% complete"
    else :
        driveMessage = str(numDrives) + " Drive(s)"


    message = imageMessage + "\n" + driveMessage
    lcd.message(message)



def runCommandAndGetStdout(cmd):
    proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    out, err = proc.communicate()
    return out


def writeImage():

    global nowWriting
    global writeStatusLine

    if len(imageNames) == 0 or len(listOfDrives) == 0:
        return

    imagingCommand = constructCommand()

    nowWriting = True


    writeStatusLine = "0"
    refreshLcd()

    process = Popen(imagingCommand, stdout=PIPE, stderr=PIPE, shell=True, executable='/bin/bash')


    lines_iterator = iter(process.stderr.readline, b"")
    for line in lines_iterator:

        line = line.rstrip()

        if writeStatusLine != line:
            writeStatusLine = line
            refreshLcd()




    nowWriting = False

    refreshLcd()






def constructCommand():
    command = "pv -n " + imagePath + "\"" +  imageNames[currentImageSelection] +  "\""
    numDrives = len(listOfDrives)

    firstDriveName = listOfDrives[0]
    firstDriveCommand = " | dd of=/dev/" + firstDriveName + " bs=1M"


    for i in range(1, numDrives):
        nextDriveCommand = " | tee >(dd of=/dev/" + listOfDrives[i] + " bs=1M)"
        command += nextDriveCommand


    command += firstDriveCommand
    print command
    return command



refreshSystem()
refreshLcd()

while True:
    time.sleep(0.15) #To debounce and prevent excessive CPU use

    if lcd.buttonPressed(lcd.UP):
        currentImageSelection += 1
        
        if currentImageSelection >= len(imageNames):
            currentImageSelection = 0

        refreshLcd()

    elif lcd.buttonPressed(lcd.DOWN):
        currentImageSelection -= 1
        
        if currentImageSelection < 0:
            currentImageSelection = len(imageNames) - 1

        refreshLcd()


    if lcd.buttonPressed(lcd.LEFT):
       refreshSystem()
       refreshLcd()
    
    elif lcd.buttonPressed(lcd.SELECT):
       powerOff()


    elif lcd.buttonPressed(lcd.RIGHT):
        writeImage()
