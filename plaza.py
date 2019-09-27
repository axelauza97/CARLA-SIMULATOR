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

actor_list = []

centerLocation=carla.Transform(location=carla.Location(x=-20.8,y=-57.9,z=0))

# Function for filter location in a radious of r
def filterLocation(variable):
    r=3
    location=centerLocation.location
    locationVariable=variable
    if locationVariable.x<=location.x+r and locationVariable.x>=location.x-r and locationVariable.y<=location.y+r and locationVariable.y>=location.y-r:
        return True
    else: 
        return False

#Fill trasnforms that will have the pedestrians
def fill_transforms(n,world):
    transforms_pedestrians=[]
    puntos =[]
    finalPoints=[]
    puntos.append(world.get_random_location_from_navigation())
    while len(finalPoints)<=n:
        punto=world.get_random_location_from_navigation()
        if not(punto in puntos):
            puntos.append(punto) 
            finalPoints=filter(filterLocation,puntos)
            if not(punto in finalPoints):
                puntos.remove(punto)
    cont=0
    print "Filling spawn positions"
    while(n!=cont):
        spawn_point = finalPoints.pop()
        if (spawn_point != None and not(spawn_point in transforms_pedestrians)):
            transforms_pedestrians.append(carla.Transform(location=spawn_point))
            cont=cont+1
    return transforms_pedestrians

# Spawn randmon pedestrians in a location  
def spawn_pedestrian(blueprint_library,world,transforms_pedestrians):
    blueprintsWalkers = blueprint_library.filter("walker.pedestrian.*")
    walker_bp = random.choice(blueprintsWalkers)
    transform=transforms_pedestrians.pop()
    human = world.try_spawn_actor(walker_bp, transform)
    if not(human is None):
        print('created %s' % human.type_id)
        return human

def add_controller(world,blueprint_library,actors):
    # 3. we spawn the walker controller
    walker_controller_bp = blueprint_library.find('controller.ai.walker')
    controllers=[]
    for human in actors:
        controller = world.spawn_actor(walker_controller_bp, carla.Transform(), attach_to=human)
        controllers.append(controller)
    world.wait_for_tick()
    for controller in controllers:
        controller.start()
        # set walk to random point
        controller.go_to_location(world.get_random_location_from_navigation())
        # random max speed
        controller.set_max_speed(0.5 + random.random())    # max speed between 1 and 2 (default is 1.4 m/s)
def callPedestrians(n,blueprint_library,world):
    transforms_pedestrians=[]
    transforms_pedestrians=fill_transforms(n,world)
    print "Spwaning pedestrians "+str(n)
    actors=[]
    for i in range(len(transforms_pedestrians)):
        actor=spawn_pedestrian(blueprint_library,world,transforms_pedestrians)     
        if not(actor is None):
            actors.append(actor)   
    print "Addign controller to pedestrians"
    add_controller(world,blueprint_library,actors)
    actor_list.extend(actors)
    print "Finish Spwaning"


def main():
    try:
        client = carla.Client('200.126.19.123', 2000)
        client.set_timeout(2.0)
        world = client.get_world()
        # WEATHER 
        weather = carla.WeatherParameters(cloudyness=0.0,precipitation=0.0,sun_altitude_angle=90.0)
        world.set_weather(weather)
        # The world contains the list blueprints that we can use for adding new
        # actors into the simulation.
        blueprint_library = world.get_blueprint_library()
        
        # Number of pedestrians 
        n=25
        callPedestrians(n,blueprint_library,world)

        # Let's add now a "depth" camera attached to the vehicle. Note that the
        # transform we give here is now relative to the vehicle.
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '1200')
        camera_bp.set_attribute('image_size_y', '700')
        camera_bp.set_attribute('sensor_tick', '0.05')
        camera_bp.set_attribute('fov', '100')
        #Center camaras
        x0=-20.8
        y0=-57.9
        #x0=centerLocation.location.x
        #y0=centerLocation.location.y
        camera_transformI = carla.Transform(carla.Location(x=x0+5,y=y0+5, z=3),carla.Rotation(pitch=-25, yaw=225, roll=0))
        camera_transformD = carla.Transform(carla.Location(x=x0+5,y=y0-5, z=3),carla.Rotation(pitch=-25, yaw=135, roll=0))
        camera_transformF = carla.Transform(carla.Location(x=x0-5,y=y0+5, z=3),carla.Rotation(pitch=-25, yaw=315, roll=0))
        camera_transformA = carla.Transform(carla.Location(x=x0-5,y=y0-5, z=3),carla.Rotation(pitch=-25, yaw=45, roll=0))

        cameraI = world.spawn_actor(camera_bp, camera_transformI)
        cameraD = world.spawn_actor(camera_bp, camera_transformD)
        cameraF = world.spawn_actor(camera_bp, camera_transformF)
        cameraA = world.spawn_actor(camera_bp, camera_transformA)

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


        time.sleep(1)
        n=10
        while True:
            global centerLocation
            centerLocation=carla.Transform(location=carla.Location(x=-52.8,y=-65.8,z=0))
            callPedestrians(n,blueprint_library,world)
            centerLocation=carla.Transform(location=carla.Location(x=-21.8,y=-32.4,z=0))
            callPedestrians(n,blueprint_library,world)
            centerLocation=carla.Transform(location=carla.Location(x=-38.9,y=-96.0,z=0))
            callPedestrians(n,blueprint_library,world)
            time.sleep(1)

    finally:
        
        print('destroying actors')
        for actor in actor_list:
            actor.destroy()
        print('done.')


if __name__ == '__main__':
    if isdir('outA/')  or isdir('outD/') or isdir('outF/') or isdir('outI/'):
        shutil.rmtree('outA')
        shutil.rmtree('outD')
        shutil.rmtree('outF')
        shutil.rmtree('outI')
    main()
