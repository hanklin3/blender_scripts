# Blender Scripts

Various Python scripts for rendering objects in Blender.

`render_blender.py` loads a single .obj file.
It renders the object in N different viewpoints - and for each viewpoint, M different lights.
The lights are point lights, generated randomly on a unit sphere around the object. Theta is constrainted to [-pi/2, pi/2].
For each viewpoint, it outputs Tangent surface normals and depth. 
For each light source, it outputs diffuse, specular and combined image (full render).
Tested with Blender 2.82a in Ubuntu 18.04 and Windows 10.

`batch_render_blender.py` iterates over a folder of folders containing .obj files, and executes `render_blender.py` for each such object.


