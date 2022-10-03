# This is an import script for data created by the 'Patchy Track' iOS app.

# https://www.bannaflak.com
# https://github.com/hizzlehoff/

# Still new to Blender, scripting feedback is welcome.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.


bl_info = {
    "name": "Patchy Track iOS app data importer (.txt)",
    "author": "Bannaflak",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "File > Import",
    "description": "Imports captured data drom Patchy Track iOS app",
    "warning": "",
    "doc_url": "http://www.bannaflak.com/",
    "category": "Import-Export",
}

import bpy
import math
import os
import ntpath
from math import pi
import mathutils
from mathutils import *
from math import *

def patchy_track_data_import_and_parse_data(self, context, filePath):
    
    print(">>>> importing ...")

    # Get captured data path and fileName.
    path, fileName = ntpath.split(filePath)
    
    # Open the file.
    f = open(filePath, 'r', encoding='utf-8')
    data = f.read()
    f.close()

    # Set current scene fps & base
    bpy.context.scene.render.fps = 60
    bpy.context.scene.render.fps_base = 1.0010000467300415
    fps = 59.94
    
    #bpy.context.scene.render.fps = 60
    #bpy.context.scene.render.fps_base = 1
    #fps = 60

    # Allow sub frames.
    bpy.context.scene.show_subframe = True
    
    # Deselect all.
    bpy.ops.object.select_all(action='DESELECT')
    
    # If it already exists delete the root object and it's children.
    for o in bpy.context.scene.objects:
        if o.name == "Patchy Track Root":

            self.report({"WARNING"}, "Please use this importer in an empty scene.")
            return {'CANCELLED'}

            #o.select_set(True)
            #for child in o.children:
                #print(child.name)
                #child.select_set(True)
                #bpy.data.objects[child.name].animation_data_clear()
            #bpy.ops.object.delete()

    #return {'FINISHED'} 

    # Create a root object.
    bpy.ops.object.empty_add(location=(0,0,0))
    rootObject = bpy.context.object
    rootObject.name = "Patchy Track Root"
    rootObject.rotation_mode = 'XYZ'

    # Create a camera.
    cameraData = bpy.data.cameras.new(name='Patchy Track Camera')
    cameraObject = bpy.data.objects.new('Patchy Track Camera', cameraData)    
    cameraObject.data.lens_unit = 'FOV'
    bpy.data.collections["Collection"].objects.link(cameraObject)

    # Set the camera parent.
    cameraObject.parent = rootObject

    # Deselect all.
    bpy.ops.object.select_all(action='DESELECT')

    # Select the camera.
    bpy.data.objects["Patchy Track Camera"].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Patchy Track Camera']

    # Set the camera' rotation mode to Quaternion.
    cameraObject.rotation_mode = 'QUATERNION'

    # The timer starts from 0 and the video and the data are offset.
    bpy.context.scene.frame_start = 0
    dataOffset = 2
    
    # Create the keyframes for the camera.
    lines = data.splitlines()
    for line in lines:
        v = line.split(",")

        if v[0] == "Resolution":
            width = float(v[1])
            height = float(v[2])
            bpy.context.scene.render.resolution_x = int(width)
            bpy.context.scene.render.resolution_y = int(height)

        if v[0] == "Key":            
            # Go to frame and subframe.
            currentFrame = (int(v[1]) / 1000.0) * fps
            frame = int( math.floor(currentFrame) )
            subFrame = currentFrame - frame
            print(frame, subFrame)
            bpy.context.scene.frame_set( dataOffset + frame, subframe=subFrame)

            # Set position, rotation and lens.
            bpy.data.objects["Patchy Track Camera"].location = (float(v[4]), float(v[5]), float(v[6]))
            bpy.data.objects["Patchy Track Camera"].rotation_quaternion = (float(v[10]), float(v[7]), float(v[8]), float(v[9]))

            # Set key.
            bpy.ops.anim.keyframe_insert_menu(type='LocRotScale')

            # Lens FOV
            cameraObject.data.angle = float(v[2]) * (pi / 180)
            cameraObject.data.keyframe_insert(data_path = 'lens')

    # Set end frame.
    bpy.context.scene.frame_end = frame

    # Set all keyframes to stepped.
    for fcurve in bpy.data.objects["Patchy Track Camera"].animation_data.action.fcurves:
        for keyFrame in fcurve.keyframe_points:
            keyFrame.interpolation = 'CONSTANT'

    # https://docs.blender.org/api/current/bpy.ops.html

    # Import video as background if it exists.
    videoName = fileName.split(".")[0]
    videoFileName = videoName + ".mov"
    videoPath = ntpath.join(path, videoFileName)

    if os.path.isfile(videoPath):
        bpy.context.object.data.show_background_images = True
        bpy.data.movieclips.load(videoPath)
        bg = cameraObject.data.background_images.new()
        bg.source = 'MOVIE_CLIP'
        bg.clip = bpy.data.movieclips.get(videoName)

    # Deselect all.
    bpy.ops.object.select_all(action='DESELECT')
    
    # Import geometry if it exists.
    geometryName = fileName.split(".")[0]
    geometryFileName = geometryName + ".obj"
    geometryPath = ntpath.join(path, geometryFileName)

    if os.path.isfile(geometryPath):
        result = bpy.ops.import_scene.obj(filepath=geometryPath)
        print(result)
    
        if 'FINISHED' in result:
            geometryObject = bpy.context.selected_objects[0]
            geometryObject.parent = rootObject
            geometryObject.rotation_mode = 'XYZ'

            geometryObject.rotation_euler.x = 0
            geometryObject.rotation_euler.y = 0
            geometryObject.rotation_euler.z = 0
    
    # Orient the captured data.
    rootObject.rotation_euler.x = 90 * (pi / 180)

    return {'FINISHED'}

# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

class ImportPatchyTrackData(Operator, ImportHelper):
    bl_idname = "patchy_track.import_data"
    bl_label = "Import Patchy Track iOS app data"

    # ImportHelper mixin class uses this
    filename_ext = ".txt"

    filter_glob: StringProperty(
        default="*.txt",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
    )

    def execute(self, context):
        return patchy_track_data_import_and_parse_data(self, context, self.filepath)

def menu_func_import(self, context):
    self.layout.operator(ImportPatchyTrackData.bl_idname, text="Patchy Track iOS app data imporer (.txt)")

def register():
    bpy.utils.register_class(ImportPatchyTrackData)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ImportPatchyTrackData)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.patchy_track.import_data('INVOKE_DEFAULT')
