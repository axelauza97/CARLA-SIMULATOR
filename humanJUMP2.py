#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import random
import time
import cv2
import numpy as np
from os import listdir
from os.path import isfile, join,isdir
import shutil


def main():
    actor_list = []

    # In this tutorial script, we are going to add a vehicle to the simulation
    # and let it drive in autopilot. We will also create a camera attached to
    # that vehicle, and save all the images generated by the camera to disk.

    try:
        # First of all, we need to create the client that will send the requests
        # to the simulator. Here we'll assume the simulator is accepting
        # requests in the localhost at port 2000.
        client = carla.Client('localhost', 2000)
        client.set_timeout(2.0)

        # Once we have a client we can retrieve the world that is currently
        # running.
        world = client.get_world()
        # WEATHER 
        weather = carla.WeatherParameters(cloudyness=0.0,precipitation=0.0,sun_altitude_angle=90.0)
        world.set_weather(weather)

        # The world contains the list blueprints that we can use for adding new
        # actors into the simulation.
        blueprint_library = world.get_blueprint_library()
        
        # HUMAN walker.pedestrian.0001
        bp = blueprint_library.find('walker.pedestrian.0001')
        
        # Now we need to give an initial transform to the vehicle. We choose a
        # random transform from the list of recommended spawn points of the map.
        # location of manual control
        #transform = random.choice(world.get_map().get_spawn_points())
        #a=world.get_map().get_spawn_points()
        #print(a[0])
        #heading IS Z  91SE
        transform=carla.Transform(carla.Location(x=-13.8, y=-50.1, z=0.5), carla.Rotation(pitch=0, yaw=-93, roll=0))
        # So let's tell the world to spawn the vehicle.
        human = world.spawn_actor(bp, transform)


        # It is important to note that the actors we create won't be destroyed
        # unless we call their "destroy" function. If we fail to call "destroy"
        # they will stay in the simulation even after we quit the Python script.
        # For that reason, we are storing all the actors we create so we can
        # destroy them afterwards.
        actor_list.append(human)
        print('created %s' % human.type_id)

        # Let's add now a "depth" camera attached to the vehicle. Note that the
        # transform we give here is now relative to the vehicle.
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '1200')
        camera_bp.set_attribute('image_size_y', '700')
        camera_bp.set_attribute('sensor_tick', '0.05')
        #(x=-5.5,y=4, z=1.0)
        camera_transformI = carla.Transform(carla.Location(x=0,y=4, z=1.0),carla.Rotation(pitch=3, yaw=-90, roll=0))
        camera_transformD = carla.Transform(carla.Location(x=0,y=-4, z=1.0),carla.Rotation(pitch=3, yaw=90, roll=0))
        camera_transformF = carla.Transform(carla.Location(x=5,y=0, z=1.0),carla.Rotation(pitch=5, yaw=180, roll=0))
        camera_transformA = carla.Transform(carla.Location(x=-5,y=0, z=1.0),carla.Rotation(pitch=5, yaw=0, roll=0))

        cameraI = world.spawn_actor(camera_bp, camera_transformI, attach_to=human)
        cameraD = world.spawn_actor(camera_bp, camera_transformD, attach_to=human)
        cameraF = world.spawn_actor(camera_bp, camera_transformF, attach_to=human)
        cameraA = world.spawn_actor(camera_bp, camera_transformA, attach_to=human)

        actor_list.append(cameraI)
        actor_list.append(cameraD)
        actor_list.append(cameraF)
        actor_list.append(cameraA)

        print('created %s' % cameraI.type_id)
        print('created %s' % cameraD.type_id)
        print('created %s' % cameraF.type_id)
        print('created %s' % cameraA.type_id)
        

        # Now we register the function that will be called each time the sensor
        # receives an image. In this example we are saving the image to disk
        print("Capturing images")
        cameraI.listen(lambda image: image.save_to_disk('outI/%06d.tiff' % image.frame))
        cameraD.listen(lambda image: image.save_to_disk('outD/%06d.tiff' % image.frame))
        cameraF.listen(lambda image: image.save_to_disk('outF/%06d.tiff' % image.frame))
        cameraA.listen(lambda image: image.save_to_disk('outA/%06d.tiff' % image.frame))
        #cameraA.listen(lambda image: image.save_to_disk('_out/%06dA.tiff' % image.frame))

        """control = carla.WalkerBoneControl()
        controlR=human.get_control()
        print controlR
        for x in range(0,10):
            control.jump=1
            human.apply_control(control)
            
            location = human.get_location()
            location.z += 0.5
            human.set_location(location)
            
            time.sleep(1)   """
        

        """SALTO DEFAULT
        world.tick()
        control = carla.WalkerBoneControl()
        control.speed=1
        control.direction.x=0
        control.direction.y=-1
        control.direction.z=0
        human.apply_control(control)
        time.sleep(1)
        for x in range(0,5):
            control.jump=1
            human.apply_control(control)
            world.tick()
            control.jump=0
            human.apply_control(control)
            time.sleep(3)"""
        world.tick()
        control = carla.WalkerBoneControl()
        print control


        first_tuple = ('crl_arm__R', carla.Transform(carla.Location(x=-1*0.1,y=1*0.1,z=1.5),carla.Rotation(pitch=30)))
        second_tuple = ('crl_arm__L', carla.Transform(carla.Location(x=1*0.1,y=1*0.1,z=1.5),carla.Rotation(pitch=30)))
        
        #first_tuple = ('crl_hand__R', carla.Transform(carla.Location(x=-1,y=1,z=0),carla.Rotation(roll=90)))
        #second_tuple = ('crl_hand__L', carla.Transform(carla.Location(x=-1,y=1,z=0),carla.Rotation(roll=90)))

        #second_tuple = ('crl_eye__L', carla.Transform(human.get_location(),carla.Rotation(pitch=90)))


        fr = ('crl_foreArm__R', carla.Transform(carla.Location(x=-1,y=1,z=0),carla.Rotation(pitch=-90)))
        fl = ('crl_foreArm__L', carla.Transform(carla.Location(x=1,y=1,z=0),carla.Rotation(pitch=-90)))

        #control.bone_transforms = [first_tuple, second_tuple,fr,fl]
        control.bone_transforms = [ first_tuple, second_tuple]
        human.apply_control(control)

        world.tick()
        time.sleep(1)

    finally:
        
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')


if __name__ == '__main__':
    if isdir('outI/')  and isdir('outI/') and isdir('outI/') and isdir('outI/'):
        shutil.rmtree('outA')
        shutil.rmtree('outD')
        shutil.rmtree('outF')
        shutil.rmtree('outI')
    main()
