# A script to generate data for Photometric Stereo.
# Running the script will iterate a directory with .obj files, for each object will produce V views, for each view, L lights angles

# Each object will launch blender in a different thread.

# Example:
# blender --background --python <script>
#

from math import radians
import argparse
import sys
import os
import numpy as np
import bpy


parser = argparse.ArgumentParser(description='Renders given obj file by rotation a camera around it.')
parser.add_argument('--views', type=int, default=4, help='number of views to be rendered')
parser.add_argument('-obj', type=str, help='Path to the obj file to be rendered.')
parser.add_argument('--output_folder', type=str, default='/tmp', help='The path the output will be dumped to.')
parser.add_argument('--scale', type=float, default=1, help='Scaling factor applied to model. Depends on size of mesh.')
parser.add_argument('--depth_scale', type=float, default=1.4, help='Scaling that is applied to depth. Depends on size of mesh. Try out various values until you get a good result. Ignored if format is OPEN_EXR.')
parser.add_argument('--color_depth', type=str, default='8', help='Number of bit per channel used for output. Either 8 or 16.')
parser.add_argument('-filepath', type=str, help='Path to the output')

argv = sys.argv
argv = argv[argv.index("--") + 1:]
args = parser.parse_args(argv)
# args.obj = "C:\model.obj"


# generate a point on a sphere with radius 1, not in front of the cam
def gen_samples_on_shpere_surface():
	factor = 0.5  # this causes the light not to be directly in front of the camera
	r = 1
	phi_ = np.random.random() * (2 * np.pi)  # angle in xy plane
	theta_ = np.random.random() * (factor * np.pi)  # angle from z angle
	x = r * np.cos(phi_) * np.sin(theta_)
	y = r * np.sin(phi_) * np.sin(theta_)
	z = r * np.cos(theta_)
	return x, y, z


def load_object(obj_filename):
	bpy.ops.import_scene.obj(filepath=obj_filename)
	for object in bpy.context.scene.objects:
		if object.name in ['Camera', 'Lamp']:
			continue
		bpy.context.scene.objects.active = object
		if args.scale != 1:
			bpy.ops.transform.resize(value=(args.scale, args.scale, args.scale))
			bpy.ops.object.transform_apply(scale=True)

		# remove double meshes
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.remove_doubles()
		bpy.ops.object.mode_set(mode='OBJECT')

		# bpy.ops.object.modifier_add(type='SUBSURF')
		# bpy.context.object.modifiers["Subsurf"].levels = 3
		# bpy.context.object.modifiers["Subsurf"].render_levels = 3
		# # bpy.context.object.modifiers["Subsurf"].subdivision_type = 'CATMULL_CLARK'
		# bpy.context.object.modifiers["Subsurf"].use_subsurf_uv = False

		# split edges for better quality
		bpy.ops.object.modifier_add(type='EDGE_SPLIT')
		bpy.context.object.modifiers["EdgeSplit"].split_angle = 0.523
		bpy.context.object.modifiers["EdgeSplit"].use_edge_angle = True
		bpy.context.object.modifiers["EdgeSplit"].use_edge_sharp = False
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="EdgeSplit")
		
		# object.data.use_auto_smooth = 1
		# object.data.auto_smooth_angle = np.pi/20


def setup_nodes():
	# Delete previous stuff
	for obj in bpy.data.objects:
		if obj.name in ['Camera']:
			continue
		obj.select = True
		bpy.ops.object.delete()

	# Set up rendering of depth map.
	bpy.context.scene.use_nodes = True
	tree = bpy.context.scene.node_tree
	links = tree.links

	# Add passes for additionally dumping albedo and normals.
	bpy.context.scene.render.engine = 'CYCLES'
	bpy.context.scene.cycles.device = 'GPU'
	bpy.types.CyclesRenderSettings.device = 'GPU'
	bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

	render = bpy.context.scene.render
	render.layers["RenderLayer"].use_pass_normal = True
	render.layers["RenderLayer"].use_pass_color = True
	render.image_settings.file_format = "PNG"
	render.image_settings.color_depth = args.color_depth
	render.image_settings.color_mode = "RGB"

	# color space of tangent normals
	bpy.context.scene.display_settings.display_device = 'None'

	# Clear default nodes
	for n in tree.nodes:
		tree.nodes.remove(n)

	# Create input render layer node.
	render_layers = tree.nodes.new('CompositorNodeRLayers')

	depth_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
	depth_file_output.label = 'Depth Output'

	# Remap as other types can not represent the full range of depth.
	map = tree.nodes.new(type="CompositorNodeMapValue")
	# Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
	map.offset = [-0.7]
	map.size = [args.depth_scale]
	map.use_min = True
	map.min = [0]
	links.new(render_layers.outputs['Depth'], map.inputs[0])
	links.new(map.outputs[0], depth_file_output.inputs[0])

	scale_normal = tree.nodes.new(type="CompositorNodeMixRGB")
	scale_normal.blend_type = 'MULTIPLY'
	scale_normal.use_alpha = True
	scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
	links.new(render_layers.outputs['Normal'], scale_normal.inputs[1])

	bias_normal = tree.nodes.new(type="CompositorNodeMixRGB")
	bias_normal.blend_type = 'ADD'
	# bias_normal.use_alpha = True
	bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
	links.new(scale_normal.outputs[0], bias_normal.inputs[1])

	normal_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
	normal_file_output.label = 'Normal Output'
	links.new(bias_normal.outputs[0], normal_file_output.inputs[0])

	albedo_file_output = tree.nodes.new(type="CompositorNodeOutputFile")
	albedo_file_output.label = 'Albedo Output'
	links.new(render_layers.outputs['Color'], albedo_file_output.inputs[0])

	scene = bpy.context.scene
	model_identifier = os.path.split(os.path.split(args.obj)[0])[1]
	args.filepath = os.path.join(args.output_folder, model_identifier)
	scene.render.image_settings.file_format = 'PNG'  # set output format to .png

	stepsize = 360.0 / args.views
	rotation_mode = 'XYZ'

	for output_node in [depth_file_output, normal_file_output, albedo_file_output]:
		output_node.base_path = ''

	return normal_file_output, depth_file_output, albedo_file_output


# setup size, place camera above object and "look down"
def setup_camera():
	scene = bpy.context.scene
	scene.render.resolution_x = 300  # TODO change to args
	scene.render.resolution_y = 300	 # TODO change to args
	scene.render.resolution_percentage = 100
	scene.render.alpha_mode = 'TRANSPARENT'
	cam = scene.objects['Camera']
	cam.location = (0, 0, 1)  # constant in order to generate tangent normals

	cam.rotation_euler[2] = 90
	cam.rotation_euler[0] = 0
	cam.rotation_euler[1] = 0

## MAIN
normal_file_output, depth_file_output, albedo_file_output = setup_nodes()
setup_camera()
load_object(args.obj)

stepsize = 360.0 / args.views
scene = bpy.context.scene
num_of_lights = 1

for i in range(0, args.views):
	print("Rotation {}, {}".format((stepsize * i), radians(stepsize * i)))
	file_path  = os.path.join(args.filepath, "obj_rotation" + str(i), "")

	depth_file_output.file_slots[0].path = file_path + "depth"
	normal_file_output.file_slots[0].path = file_path + "normal"
	albedo_file_output.file_slots[0].path = file_path + "albedo"

	for jj in range(num_of_lights):
		x, y, z = gen_samples_on_shpere_surface()
		scene.render.filepath = file_path + 'xyz_{:.2f}_{:.2f}_{:.2f}'.format(x, y, z)

		# create new point light
		bpy.ops.object.lamp_add(type='POINT', location=(0, 0, 0))  # was  0 0 0
		lamp = bpy.data.lamps['Point']
		lamp.shadow_method = 'RAY_SHADOW'
		lamp.energy = 0.1 #??????????????
		# Possibly disable specular shading:
		lamp.use_specular = True

		bpy.data.objects['Point'].select = True
		bpy.ops.transform.translate(value=(x, y, z))

		bpy.ops.render.render(write_still=True)  # render still

		# delete light
		bpy.data.objects['Point'].select = True
		bpy.ops.object.delete()

	for obj in bpy.data.objects:
		if obj.name in ['Point', 'Camera']:
			continue
		else:
			objct = obj

	# objct.rotation_euler[2] += radians(stepsize)
	objct.rotation_euler[0] += radians(stepsize / 2)

