# Patch Track iOS app data importer for Maya v1.0
import maya.cmds as cmds
import maya.api.OpenMaya as api
import math
import os
#import maya.mel

# Todo: Warn user if scene not set to CM, warn user about framerate not being 60 fps?
# AEinvokeFitRezGate PT_test1Shape1->imagePlaneShape1.sizeX PT_test1Shape1->imagePlaneShape1.sizeY;

def PTSetKeyframe(data, fps, scaleFactor, object):
    
    cmds.select(object)

    keyFrameTime = (float(data[0]) /1000.0) * fps
    cmds.currentTime( keyFrameTime )

    quat = api.MQuaternion(float(data[4]),float(data[5]),float(data[6]),float(data[7]))
    euler = quat.asEulerRotation()

    cmds.setKeyframe(v=float(data[1]) * scaleFactor, at='translateX')
    cmds.setKeyframe(v=float(data[2]) * scaleFactor, at='translateY')
    cmds.setKeyframe(v=float(data[3]) * scaleFactor, at='translateZ')

    cmds.setKeyframe(v=euler[0] * (180/math.pi), at='rotateX')
    cmds.setKeyframe(v=euler[1] * (180/math.pi), at='rotateY')
    cmds.setKeyframe(v=euler[2] * (180/math.pi), at='rotateZ')

    return int(round(keyFrameTime))

def PTUpdateOutput(message):
    cmds.scrollField("PTOutput", edit=True, tx=message)
    cmds.refresh()

def PTImport(*args):
    
    sceneScale = cmds.floatField("PTSceneScaleField", q=True, v=True)
    fps = cmds.currentTime('1sec', edit=True)

    filePath = cmds.fileDialog2(fileMode=1, caption="Select QuestCapture Capture...")[0]
    
    # Create camera and import the animation.
    with open(filePath, 'r') as file1:
        
        fileName = os.path.basename(filePath)
        name, extension = os.path.splitext(fileName)
        name = name.replace("-","_") + "1"

        progressMessage = "Please wait, importing"
        PTUpdateOutput(progressMessage)

        if cmds.objExists(name):
            cmds.delete(name)

        cameraObject = cmds.camera(n=name)
        imagePlane = cmds.imagePlane(camera=cameraObject[1])
        
        lastKeyframeTime = 0

        for line in file1:
            line = line.strip()
            if '#' not in line[0]:
                items = line.split(',')
                if 'FocalLength' == items[0]:
                    cmds.setAttr(cameraObject[1] + ".focalLength", float(items[1]))
                elif 'ScreenSize' == items[0]:
                    cmds.setAttr("defaultResolution.width", int(float(items[1])))
                    cmds.setAttr("defaultResolution.height", int(float(items[2])))
                elif 'K' == items[0]:
                    lastKeyframeTime = PTSetKeyframe(items[1:], fps, sceneScale, cameraObject)

        cmds.scrollField("PTOutput", edit=True, tx="Unfortunately ARKit reports incorrect focal length data for some devices at the moment.\n\nFor iPhone X use 20.78mm, for iPad Pro use 29.00mm for other devices estimate.\n")
    
    # Import the obj file if it exists
    objPath = filePath.replace(".txt",".obj")
    if os.path.exists(objPath):
        cmds.file(objPath, i=True)

    # Import the video file if it exists and setup the image planes
    videoPath = filePath.replace(".txt",".mov")
    if os.path.exists(videoPath):
        cmds.setAttr(cameraObject[1]+".displayResolution", 1)

        cmds.setAttr(str(imagePlane[0])+".type", 2)
        cmds.setAttr(str(imagePlane[0])+".imageName", videoPath, type="string")
        cmds.refresh()

        videoEndFrame = cmds.getAttr(str(imagePlane[0])+".frameOut")

        cmds.playbackOptions(minTime = 1)
        cmds.playbackOptions(animationStartTime = 1)

        cmds.playbackOptions(maxTime = lastKeyframeTime)
        cmds.playbackOptions(animationEndTime = lastKeyframeTime)

def PTImporterWindow():

    if cmds.window("PatchyTrackWindow", exists = True):
        cmds.deleteUI("PatchyTrackWindow")
    
    window = cmds.window("PatchyTrackWindow", title="Patchy Track Importer.", iconName='PatchyTrack', widthHeight=(300, 60), sizeable=False )
    cmds.window("PatchyTrackWindow", e=True, w=300, h=60)
    
    cmds.columnLayout( adjustableColumn=True)

    cmds.rowLayout( numberOfColumns=2, columnWidth2=(150,150), adjustableColumn=2)
    cmds.text('Scene Scale')
    cmds.floatField("PTSceneScaleField", value=1.0)
    cmds.setParent( '..' )

    cmds.rowLayout( numberOfColumns=1, adjustableColumn=1)
    cmds.button( label='Import data', command=PTImport)
    cmds.setParent( '..' )

    cmds.rowLayout()
    cmds.scrollField("PTOutput", w=320, h=100, editable = False, tx="...", wordWrap = True)
    cmds.setParent( '..' )

    cmds.showWindow( window )

PTImporterWindow()
