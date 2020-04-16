# a script for batch rendering multiple objects
# The script will run a render script per object

import sys, os
import os.path
import argparse
from platform import system
import subprocess


parser = argparse.ArgumentParser(description='Execute render script on multiple obj files')
parser.add_argument('-path', type=str, help='Path to the directory which holds object files (in their directories')
parser.add_argument('-output_path', type=str, default="/home/toky/asaf/rendered_data/", help='Path to the directory which renders will be written in')
parser.add_argument('-max_objects', type=int, default=3, help='maximum number of objects to be rendered')
parser.add_argument('-render_script', type=str, default="render_blender.py", help='Rendering script')

args = parser.parse_args()
max_objects = args.max_objects
objects_dir = args.path


if system() == 'Windows':
    blender_path = 'C:\Program Files\Blender Foundation\Blender 2.82'
    blender_exec = os.path.join(blender_path, 'blender.exe')
    blender_exec = ('\"' + blender_exec + '\" ')  # fixes windows spaces in directories
else: # linux
    # blender_path = '/home/blender/'
    # blender_exec = os.path.join(blender_path, 'blender', 'blender')
    # blender_exec = "blender "  # if installed using snap-store or has an alias
    blender_exec = "~/blender/blender-2.82a-linux64/blender "
object_files = []

path, dirs, files = next(os.walk(objects_dir))
for dir_ in dirs:
    obj_path, obj_dirs, obj_files = next(os.walk(os.path.join(objects_dir,dir_)))
    for file in obj_files:
        if file.endswith(".obj"):
            object_files.append(os.path.join(obj_path, file))

if not os.path.isfile(args.render_script):
    quit("Can't find render_blender script")
for idx, obj_file in enumerate(object_files):
    run_cmd = blender_exec + " -b -P " + args.render_script+ " -- -obj " + obj_file + " -output_folder " + args.output_path
    print(run_cmd)
    
    # make sure no errors are raised during run. If some error is raised, quit
    try:
        a = subprocess.check_call(run_cmd, shell=True)
    except subprocess.CalledProcessError as error:
        quit("Error during run: {}".format(error))

    if idx == max_objects:
        break


