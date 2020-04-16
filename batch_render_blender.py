# a script for batch rendering multiple objects
# The script will run a render script per object

import sys, os
import os.path
import argparse
from platform import system
import subprocess
import logging

LOG_FORMAT = "%(asctime)s %(message)s"
logging.basicConfig(
            filename='batch_render.log', 
            level=logging.DEBUG,
            format=LOG_FORMAT)


parser = argparse.ArgumentParser(description='Execute render script on multiple obj files')
parser.add_argument('-path', type=str, help='Path to the directory which holds object files (in their directories')
parser.add_argument('--views', type=int, default=5, help='number of views to be rendered for each object')
parser.add_argument('-output_path', type=str, default="/home/toky/asaf/rendered_data/", help='Path to the directory which renders will be written in')
parser.add_argument('-max_objects', type=int, default=-1, help='maximum number of objects to be rendered')
parser.add_argument('-render_script', type=str, default="render_blender.py", help='Rendering script')
parser.add_argument('-max_render_time_per_view', type=int, default=600, help='max time for single object to be rendered')

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

logging.info("Started rendering sequence, saving results in {}".format(args.output_path))
for idx, obj_file in enumerate(object_files):
    run_cmd = blender_exec + " -b -P " + args.render_script+ " -- -obj " + obj_file + " -output_folder " + args.output_path
    # print(run_cmd)
    logging.info("Rendering the following object:")
    logging.info(obj_file)
    
    # make sure no errors are raised during run. If some error is raised, quit
    # If a specific render runs more than args.max_render_time_per_view * views minutes, stop it
    try:
        a = subprocess.check_call(run_cmd, shell=True, timeout=args.max_render_time_per_view * args.views)
    except subprocess.CalledProcessError as error:
        logging.error("The following command caused an error: {}".format(run_cmd))
        quit("Error during run: {}".format(error))
    except subprocess.TimeoutExpired:
        logging.error("The object {} timed out and was stopped".format(obj_file))

    if idx == max_objects:
        break


