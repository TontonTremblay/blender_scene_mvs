# blender_scene_mvs
Adding a multiview system to a blender scene from a single script. 


## Using the script
This script assumes you already know a little bit about using the GUI in Blender. 
Open the python editor, copy and paste the file `place_cameras_render.py`. 

At the top of the file you need to specify which object you want to center, it is called `target_object_name`, just add the name of the object you want to place cameras around. 
By default it will generate cameras in a north hemisphere around that object, you might need to play with radius. The cameras will be generated inside a collection called `cameras`.

![image](https://github.com/TontonTremblay/blender_scene_mvs/assets/5629088/762813a8-092c-4b7a-90d5-0d01e3f9a0c5)
I added 3 different camera patterns: `random`, `structured`, `sweaping`. See figure below. 

```python
#### variables to be set ####

target_object_name = 'cam_target'
radius_around_object = 0.6
nb_cameras = 200
radius = 1

dont_render = False

# choices: random, structured, sweaping 
sampling_method = 'structured'

bpy.context.scene.render.resolution_x = 1024  # width
bpy.context.scene.render.resolution_y = 1024  # height

camera_lens = 25

# output
filepath = os.path.join('E:\\', 'download', 'the_shed', 'the_shed', 'renders')
bpy.context.scene.render.image_settings.file_format = 'PNG'  # Example format

collection_name = "cameras"
```
## Example

![mvs](https://github.com/TontonTremblay/blender_scene_mvs/assets/5629088/17a29e17-21d8-454a-8fa8-29d4bea1aabf)


Here is an example of a multivew scene, [the_shed](https://drive.google.com/file/d/1RS5Q5bBqrgxPcV6_fmxgiALwOQGo9KIz/view?usp=sharing). 
The original scene was downloaded [here](https://polyhaven.com/collections/the_shed) and see above for the 100 views that I rendered. 






