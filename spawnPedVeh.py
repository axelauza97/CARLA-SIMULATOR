#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""Spawn NPCs into the simulation"""

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

import argparse
import logging
import random
import time
from os import listdir
from os.path import isfile, join,isdir
import shutil

#DEFINE EL CENTRO DE LA POSICION DE LAS CAMARAS
centerLocation=carla.Transform(location=carla.Location(x=5.2,y=-135.2,z=0))
cameraList=[]

def filterLocation(variable):
    location=centerLocation.location
    locationVariable=variable.location
    if locationVariable.x<=location.x+40 and locationVariable.x>=location.x-40:
        return True
    else: 
        return False

def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-n', '--number-of-vehicles',
        metavar='N',
        default=20,
        type=int,
        help='number of vehicles (default: 20)')
    argparser.add_argument(
        '-w', '--number-of-walkers',
        metavar='W',
        default=50,
        type=int,
        help='number of walkers (default: 50)')
    argparser.add_argument(
        '--safe',
        action='store_true',
        help='avoid spawning vehicles prone to accidents')
    argparser.add_argument(
        '--filterv',
        metavar='PATTERN',
        default='vehicle.*',
        help='vehicles filter (default: "vehicle.*")')
    argparser.add_argument(
        '--filterw',
        metavar='PATTERN',
        default='walker.pedestrian.*',
        help='pedestrians filter (default: "walker.pedestrian.*")')
    args = argparser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    vehicles_list = []
    walkers_list = []
    all_id = []
    client = carla.Client(args.host, args.port)
    client.set_timeout(2.0)

    try:

        world = client.get_world()
        world = client.get_world()
        # WEATHER 
        weather = carla.WeatherParameters(cloudyness=0.0,precipitation=0.0,sun_altitude_angle=90.0)
        world.set_weather(weather)

        blueprints = world.get_blueprint_library().filter(args.filterv)
        blueprintsWalkers = world.get_blueprint_library().filter(args.filterw)

        if args.safe:
            blueprints = [x for x in blueprints if int(x.get_attribute('number_of_wheels')) == 4]
            blueprints = [x for x in blueprints if not x.id.endswith('isetta')]
            blueprints = [x for x in blueprints if not x.id.endswith('carlacola')]

        puntos = world.get_map().get_spawn_points()
        spawn_points=filter(filterLocation,puntos)
        number_of_spawn_points = len(spawn_points)

        if args.number_of_vehicles < number_of_spawn_points:
            random.shuffle(spawn_points)
        elif args.number_of_vehicles > number_of_spawn_points:
            msg = 'requested %d vehicles, but could only find %d spawn points'
            logging.warning(msg, args.number_of_vehicles, number_of_spawn_points)
            args.number_of_vehicles = number_of_spawn_points

        # @todo cannot import these directly.
        SpawnActor = carla.command.SpawnActor
        SetAutopilot = carla.command.SetAutopilot
        FutureActor = carla.command.FutureActor

        # --------------
        # Spawn vehicles
        # --------------
        print "Spawning vehicles"
        batch = []
        for n, transform in enumerate(spawn_points):
            if n >= args.number_of_vehicles:
                break
            blueprint = random.choice(blueprints)
            if blueprint.has_attribute('color'):
                color = random.choice(blueprint.get_attribute('color').recommended_values)
                blueprint.set_attribute('color', color)
            if blueprint.has_attribute('driver_id'):
                driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
                blueprint.set_attribute('driver_id', driver_id)
            blueprint.set_attribute('role_name', 'autopilot')
            batch.append(SpawnActor(blueprint, transform).then(SetAutopilot(FutureActor, True)))

        for response in client.apply_batch_sync(batch):
            if response.error:
                logging.error(response.error)
            else:
                vehicles_list.append(response.actor_id)

        # -------------
        # Spawn Walkers
        # -------------
        # 1. take all the random locations to spawn
        spawn_points = []
        for i in range(args.number_of_walkers):
            spawn_point = carla.Transform()
            loc = world.get_random_location_from_navigation()
            if (loc != None):
                spawn_point.location = loc
                spawn_points.append(spawn_point)

        print "Spawning pedestrians"
        # 2. we spawn the walker object
        batch = []
        for spawn_point in spawn_points:
            walker_bp = random.choice(blueprintsWalkers)
            # set as not invencible
            if walker_bp.has_attribute('is_invincible'):
                walker_bp.set_attribute('is_invincible', 'false')
            batch.append(SpawnActor(walker_bp, spawn_point))
        results = client.apply_batch_sync(batch, True)
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
            else:
                walkers_list.append({"id": results[i].actor_id})
        print "Spawning controllers for pedestrians"
        # 3. we spawn the walker controller
        batch = []
        walker_controller_bp = world.get_blueprint_library().find('controller.ai.walker')
        for i in range(len(walkers_list)):
            batch.append(SpawnActor(walker_controller_bp, carla.Transform(), walkers_list[i]["id"]))
        results = client.apply_batch_sync(batch, True)
        for i in range(len(results)):
            if results[i].error:
                logging.error(results[i].error)
            else:
                walkers_list[i]["con"] = results[i].actor_id
        # 4. we put altogether the walkers and controllers id to get the objects from their id
        for i in range(len(walkers_list)):
            all_id.append(walkers_list[i]["con"])
            all_id.append(walkers_list[i]["id"])
        all_actors = world.get_actors(all_id)

        # wait for a tick to ensure client receives the last transform of the walkers we have just created
        world.wait_for_tick()

        # 5. initialize each controller and set target to walk to (list is [controler, actor, controller, actor ...])
        for i in range(0, len(all_id), 2):
            # start walker
            all_actors[i].start()
            # set walk to random point
            all_actors[i].go_to_location(world.get_random_location_from_navigation())
            # random max speed
            all_actors[i].set_max_speed(1 + random.random())    # max speed between 1 and 2 (default is 1.4 m/s)

        print('spawned %d vehicles and %d walkers, press Ctrl+C to exit.' % (len(vehicles_list), len(walkers_list)))

        blueprint_library = world.get_blueprint_library()
        # Let's add now a "depth" camera attached to the vehicle. Note that the
        # transform we give here is now relative to the vehicle.
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '1200')
        camera_bp.set_attribute('image_size_y', '700')
        camera_bp.set_attribute('sensor_tick', '0.05')
        camera_bp.set_attribute('fov', '100')
        #(x=-5.5,y=4, z=1.0)

        camera_transformI = carla.Transform(carla.Location(x=0+5.2,y=4-135.2, z=8),carla.Rotation(pitch=-30, yaw=-90, roll=0))
        camera_transformD = carla.Transform(carla.Location(x=0+5.2,y=-4-135.2, z=8),carla.Rotation(pitch=-30, yaw=90, roll=0))
        camera_transformF = carla.Transform(carla.Location(x=5+5.2,y=0-135.2, z=8),carla.Rotation(pitch=-30, yaw=180, roll=0))
        camera_transformA = carla.Transform(carla.Location(x=-5+5.2,y=0-135.2, z=8),carla.Rotation(pitch=-30, yaw=0, roll=0))

        cameraI = world.spawn_actor(camera_bp, camera_transformI)
        cameraD = world.spawn_actor(camera_bp, camera_transformD)
        cameraF = world.spawn_actor(camera_bp, camera_transformF)
        cameraA = world.spawn_actor(camera_bp, camera_transformA)

        
        cameraList.append(cameraI)
        cameraList.append(cameraD)
        cameraList.append(cameraF)
        cameraList.append(cameraA)

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


        time.sleep(30)

    finally:
    	print "Destroying cameras"
    	for camera in cameraList:
            camera.destroy()

        print('\ndestroying %d vehicles' % len(vehicles_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in vehicles_list])

        # stop walker controllers (list is [controler, actor, controller, actor ...])
        for i in range(0, len(all_id), 2):
            all_actors[i].stop()

        print('\ndestroying %d walkers' % len(walkers_list))
        client.apply_batch([carla.command.DestroyActor(x) for x in all_id])


if __name__ == '__main__':
	try:
		if isdir('outA/')  or isdir('outD/') or isdir('outF/') or isdir('outI/'):
			shutil.rmtree('outA')
			shutil.rmtree('outD')
			shutil.rmtree('outF')
			shutil.rmtree('outI')
		main()
	except KeyboardInterrupt:
		pass
	finally:
		print('\ndone.')
