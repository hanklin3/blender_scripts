# a script for batch rendering multiple objects
# The script will run a render script per object

import sys, os
import argparse
from platform import system

parser = argparse.ArgumentParser(description='Execute render script on multiple obj files')
parser.add_argument('-path', type=str, help='Path to the directory which holds object files (in their directories')
parser.add_argument('-max_objects', type=int, default=-1, help='maximum number of objects to be rendered')
args = parser.parse_args(sys.argv)

max_objects = args.max_objects
objects_dir = args.path


if system() == 'Windows':
    blender_path = 'C:\Program Files\Blender Foundation'
    blender_exec = os.path.join(blender_path, 'blender', 'blender.exe')
    blender_exec = ('\"' + blender_exec + '\" ')  # fixes windows spaces in directories
else: # linux
    # blender_path = '/home/blender/'
    # blender_exec = os.path.join(blender_path, 'blender', 'blender')
    blender_exec = "blender "  # if installed using snap-store or has an alias

object_files = []

path, dirs, files = next(os.walk(objects_dir))
for dir_ in dirs:
    obj_path, obj_dirs, obj_files = next(os.walk(os.path.join(objects_dir,dir_)))
    for file in obj_files:
        if file.endswith(".obj"):
            object_files.append(os.path.join(obj_path, file))


for idx, obj_file in enumerate(object_files):
    run_cmd = blender_exec + "-b -P render_blender.py -- -obj " + obj_file
    print(run_cmd)
    os.system(run_cmd)
    if idx == max_objects:
        break


