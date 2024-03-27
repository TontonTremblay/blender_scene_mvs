import os 
import bpy
import json 
import numpy as np
from mathutils import Vector, Matrix
import mathutils



#### variables to be set ####

target_object_name = 'cam_target'
radius_around_object = 0.6
nb_cameras = 200
radius = 1

# choices: random, structured, sweaping 
sampling_method = 'structured'

bpy.context.scene.render.resolution_x = 1024  # width
bpy.context.scene.render.resolution_y = 1024  # height

camera_lens = 25

# output
filepath = os.path.join('E:\\', 'download', 'the_shed', 'the_shed', 'renders')
bpy.context.scene.render.image_settings.file_format = 'PNG'  # Example format


collection_name = "cameras"
collections = bpy.data.collections  # Get all collections
collection = collections.get(collection_name)

# If the collection does not exist, create it
if collection is None:
    collection = collections.new(name=collection_name)
    # Link the new collection to the scene's collection
    bpy.context.scene.collection.children.link(collection)


##############################################################################################################
# Function taken from https://github.com/zhenpeiyang/HM3D-ABO/blob/master/my_blender.py
def get_3x4_RT_matrix_from_blender(cam):
    # bcam stands for blender camera
    # R_bcam2cv = Matrix(
    #     ((1, 0,  0),
    #     (0, 1, 0),
    #     (0, 0, 1)))

    # Transpose since the rotation is object rotation, 
    # and we want coordinate rotation
    # R_world2bcam = cam.rotation_euler.to_matrix().transposed()
    # T_world2bcam = -1*R_world2bcam @ location
    #
    # Use matrix_world instead to account for all constraints
    location, rotation = cam.matrix_world.decompose()[0:2]
    R_world2bcam = rotation.to_matrix().transposed()

    # Convert camera location to translation vector used in coordinate changes
    # T_world2bcam = -1*R_world2bcam @ cam.location
    # Use location from matrix_world to account for constraints:     
    T_world2bcam = -1*R_world2bcam @ location

    # # Build the coordinate transform matrix from world to computer vision camera
    # R_world2cv = R_bcam2cv@R_world2bcam
    # T_world2cv = R_bcam2cv@T_world2bcam

    # put into 3x4 matrix
    RT = mathutils.Matrix((
        R_world2bcam[0][:] + (T_world2bcam[0],),
        R_world2bcam[1][:] + (T_world2bcam[1],),
        R_world2bcam[2][:] + (T_world2bcam[2],)
        ))
    return RT

def get_sensor_size(sensor_fit, sensor_x, sensor_y):
    if sensor_fit == 'VERTICAL':
        return sensor_y
    return sensor_x

# BKE_camera_sensor_fit
def get_sensor_fit(sensor_fit, size_x, size_y):
    if sensor_fit == 'AUTO':
        if size_x >= size_y:
            return 'HORIZONTAL'
        else:
            return 'VERTICAL'
    return sensor_fit

# Build intrinsic camera parameters from Blender camera data
#
# See notes on this in 
# blender.stackexchange.com/questions/15102/what-is-blenders-camera-projection-matrix-model
# as well as
# https://blender.stackexchange.com/a/120063/3581
def get_calibration_matrix_K_from_blender(camd):
    if camd.type != 'PERSP':
        raise ValueError('Non-perspective cameras not supported')
    scene = bpy.context.scene
    f_in_mm = camd.lens
    scale = scene.render.resolution_percentage / 100
    resolution_x_in_px = scale * scene.render.resolution_x
    resolution_y_in_px = scale * scene.render.resolution_y
    sensor_size_in_mm = get_sensor_size(camd.sensor_fit, camd.sensor_width, camd.sensor_height)
    sensor_fit = get_sensor_fit(
        camd.sensor_fit,
        scene.render.pixel_aspect_x * resolution_x_in_px,
        scene.render.pixel_aspect_y * resolution_y_in_px
    )
    pixel_aspect_ratio = scene.render.pixel_aspect_y / scene.render.pixel_aspect_x
    if sensor_fit == 'HORIZONTAL':
        view_fac_in_px = resolution_x_in_px
    else:
        view_fac_in_px = pixel_aspect_ratio * resolution_y_in_px
    pixel_size_mm_per_px = sensor_size_in_mm / f_in_mm / view_fac_in_px
    s_u = 1 / pixel_size_mm_per_px
    s_v = 1 / pixel_size_mm_per_px / pixel_aspect_ratio

    # Parameters of intrinsic calibration matrix K
    u_0 = resolution_x_in_px / 2 - camd.shift_x * view_fac_in_px
    v_0 = resolution_y_in_px / 2 + camd.shift_y * view_fac_in_px / pixel_aspect_ratio
    skew = 0 # only use rectangular pixels

    K = Matrix(
        ((s_u, skew, u_0),
        (   0,  s_v, v_0),
        (   0,    0,   1)))

    return K




def delete_cameras_with_prefix_in_collection(collection_name="cameras", prefix="cam_"):
    # Check if the collection exists
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        print(f"Collection '{collection_name}' not found.")
        return

    # Gather all camera objects with the specified prefix in their names within the collection
    cameras_to_delete = [obj for obj in collection.objects if obj.type == 'CAMERA' and obj.name.startswith(prefix)]
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    
    # Ensure we're operating in the correct context
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
            break
    
    # Select and delete each camera
    for camera in cameras_to_delete:
        # Make the current object active and select it
        bpy.context.view_layer.objects.active = camera
        camera.select_set(True)
        
        # Delete the selected object
        bpy.ops.object.delete()



def create_camera_looking_at(position, obj_name,name_camera,lens=50):

    bpy.ops.object.camera_add(location=position)  
    camera_object = bpy.context.object
    camera_object.name =name_camera 
    camera_object.scale = (0.2,0.2,0.2)
    camera_object.data.lens = lens
    camera_object.data.type = 'PERSP'

    # Ensure the target object exists
    target_object = bpy.data.objects.get(obj_name)
    
    if target_object is None:
        print(f"Object named '{obj_name}' not found.")
        return
    
    # Create a constraint that makes the camera look at the target object
    track_constraint = camera_object.constraints.new(type='TRACK_TO')
    track_constraint.target = target_object
    track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    track_constraint.up_axis = 'UP_Y'
    
    # Update the scene (in case it's not auto-updating)
    bpy.context.view_layer.update()

    return camera_object

def sweaping_hemisphere(n_samples):
    theta = np.linspace(0, 2*np.pi, n_samples)  # Parameter for the line, making a full loop around the sphere

    # To ensure the line stays on the sphere, adjust phi instead of z directly
    # Add a sinusoidal variation to phi over theta to create interesting patterns on the sphere
    # phi = np.pi / 2 + 0.9 * np.sin(4.25 * theta)  # Sinusoidal variation around the equator
    phi = np.pi / 5 * (2 + np.sin(4.25 * theta))

    # Calculate the coordinates of the line on the sphere using spherical coordinates
    x_line = radius * np.sin(phi) * np.cos(theta)
    y_line = radius * np.sin(phi) * np.sin(theta)
    z_line = radius * np.cos(phi)

    return x_line,y_line,z_line

def sample_hemisphere(n_samples):
    theta = np.random.uniform(0, 2*np.pi, n_samples)  # Azimuth angle
    # Ensure that we don't sample the very top by reducing the range of phi slightly
    phi = np.random.uniform(0, np.pi/2 - 0.01, n_samples)  # Polar angle, avoiding the North Pole

    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)

    return x, y, z

def fibonacci_hemisphere_points_upper(nb_points):
    indices = np.arange(0, nb_points, dtype=float) + 0.5

    # Adjust phi calculation to limit points to the upper hemisphere
    phi = np.arccos(1 - 2 * indices / nb_points)
    # Keep only the top half
    valid_indices = phi <= np.pi / 2
    phi = phi[valid_indices]
    # Recalculate nb_points based on valid_indices to adjust theta accordingly
    adjusted_nb_points = len(phi)
    theta = np.pi * (1 + 5**0.5) * np.arange(adjusted_nb_points)

    x = np.sin(phi) * np.cos(theta)
    y = np.sin(phi) * np.sin(theta)
    z = np.cos(phi)

    return x, y, z


#### setting up the cameras ####

target_object = bpy.data.objects.get(target_object_name)
cameras_to_render = []

if sampling_method == 'structured':
    x_line,y_line,z_line = fibonacci_hemisphere_points_upper(nb_cameras)
elif sampling_method == 'random':
    x_line,y_line,z_line = sample_hemisphere(nb_cameras)
else:
    x_line,y_line,z_line =sweaping_hemisphere(nb_cameras)

delete_cameras_with_prefix_in_collection()

for i in range(len(x_line)):

    cam = create_camera_looking_at(
        (x_line[i]+target_object.location.x,
         y_line[i]+target_object.location.y,
         z_line[i]+target_object.location.z
        ), 
        target_object_name,
        f'cam_{str(i).zfill(3)}',
        lens= camera_lens,
    )
    cameras_to_render.append(cam)
    # break

###### rendering ######

bpy.context.scene.camera = cameras_to_render[0]
bpy.context.view_layer.update()


K = get_calibration_matrix_K_from_blender(cameras_to_render[0].data)

to_export = {
    'fx': K[0][0],
    'fy': K[1][1],
    'cx': K[0][-1],
    'cy': K[1][-1],
    'camera_angle_x': cameras_to_render[0].data.angle_x,
    "aabb": [
        [
            0.5,
            0.5,
            0.5
        ],
        [
            -0.5,
            -0.5,
            -0.5
        ]
    ],
    'frames':[]
}

suffix_naming = ""

for i_cam, camera in enumerate(cameras_to_render):
    bpy.context.scene.camera = camera
    bpy.context.view_layer.update()

    rt = get_3x4_RT_matrix_from_blender(bpy.context.scene.camera)
    pos, rt, scale = bpy.context.scene.camera.matrix_world.decompose()
    rt = rt.to_matrix()
    matrix = []
    for i in range(3):
        a = []
        for j in range(3):
            a.append(rt[i][j])
        a.append(pos[i])
        matrix.append(a)
    matrix.append([0,0,0,1])

    to_add = {\
    "file_path":f'{str(i_cam).zfill(3)}{suffix_naming}.png',
    "transform_matrix":matrix
    }
    bpy.context.scene.render.filepath = f"{filepath}/{str(i_cam).zfill(3)}{suffix_naming}.png"
    if not os.path.exists(bpy.context.scene.render.filepath):
        bpy.ops.render.render(write_still = True)

    
    to_export['frames'].append(to_add)


with open(f'{filepath}/transforms.json', 'w') as f:
    json.dump(to_export, f,indent=4)

