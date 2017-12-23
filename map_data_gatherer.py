#!/usr/bin/python
# Created by Makamoto (teamwork.tf)
import time
import json
import glob, re, os, subprocess
import hashlib
from vmf_parser import VMFParser
from process.functions import MapStatsCoordinator

class MapDataGatherer(object):
	"""
	MapDataGatherer is a stateless utility object, which provides metadata from .bsp files. This metadata can be used for the automation of camera angles in-game for TF2 or other Source Engine games.
	
	Currently only Windows compatible, but should work on Linux with a few minor adjustments. Not multithreading compatible.

	Required installs:
	- Java
	- BSPSource (the jar must be placed in the same dir)
	"""

	def __init__(self, java_exec=''):
		"""
		Contructor
		"""
		self.java_exec = java_exec
		self.vmf_parser = VMFParser()
		self.map_stats_coordinator = MapStatsCoordinator()
		

	def gatherMetadataFromBSPDir(self, maps_dir='.', metadata_output_filename='output.json', scale_optimizer=(1920, 1080)):
		"""
		Analyze all .bsp files in the given directory, by decompiling them and storing the valueable metadata in our ./metadata/ folder.
		"""
		self.__generateVMFFilesFromBSPs(maps_dir)
		maps = self.__getAllMapsInFolder(maps_dir)
		maps_metadata = {}

		i = 0
		for map_name in maps:
			print("Processing map {} ({}/{})".format(map_name, i, len(maps)))
			i += 1
			vmf_obj = self.__getVMFObj(maps_dir, map_name)
			# Construct the metadata object.
			maps_metadata[map_name] = {}
			maps_metadata[map_name]["normalizedMapName"] 		= self.map_stats_coordinator.helperNormalizeMapName(map_name)
			maps_metadata[map_name]["dimensions"] 				= self.__getDimensionsOfMap(vmf_obj, scale_optimizer, method='entities')
			maps_metadata[map_name]["cameras"] 					= self.__getCameras(vmf_obj)
			maps_metadata[map_name]["skyboxCamera"] 			= self.__getEntityCoordsByClassName(vmf_obj, 'sky_camera')
			maps_metadata[map_name]["tournamentStage"] 			= self.__getEntityCoordsByModelname(vmf_obj, 'competitive_stage')
			maps_metadata[map_name]["version"] 					= self.__getMapVersion(vmf_obj)
			maps_metadata[map_name]["entityCount"] 				= self.__getEntityCount(vmf_obj)
			maps_metadata[map_name]["healthKits"] 				= self.__getHealthKits(vmf_obj)
			maps_metadata[map_name]["ammoPacks"] 				= self.__getAmmoPacks(vmf_obj)
			maps_metadata[map_name]["controlPoints"] 			= self.__getControlPoints(vmf_obj)
			maps_metadata[map_name]["briefCases"] 				= self.__getBriefCases(vmf_obj)
			maps_metadata[map_name]["spawnPoints"] 				= self.__getSpawnPoints(vmf_obj)
			maps_metadata[map_name]["resupplyLockers"] 			= self.__getResupplyLockers(vmf_obj)
			maps_metadata[map_name]["containsHalloweenProps"] 	= self.__containsHalloweenProps(vmf_obj)
			maps_metadata[map_name]["fileHash"] 				= self.__getHashForMap(maps_dir, map_name)


		self.__saveMetadataToDisk(maps_metadata, metadata_output_filename)
		print("Completed the metadata extraction for folder {}".format(maps_dir))

	def __generateVMFFilesFromBSPs(self, maps_dir):
		print("[BSPSource] Now creating VMF files, this might take a while ...")
		if os.name == 'nt':
			cmd = "start /wait cmd /c {} {} {} {} \"{}\"".format(self.java_exec, '-jar', 'bspsrc.jar', '-r', maps_dir)
		else:
			cmd = "{} {} {} {} \"{}\"".format(self.java_exec, '-jar', 'bspsrc.jar', '-r', maps_dir)
		print(cmd)
		os.system(cmd)
		print("[BSPSource] Finished converting all BSP files to VMF.")
		return

	def __getAllMapsInFolder(self, maps_dir):
		maps = []
		full_path_maps = glob.glob("{}{}*_d.vmf".format(maps_dir, os.sep))
		for full_path_map in full_path_maps:
			path_parts = full_path_map.split(os.sep)
			map_name = path_parts[-1].split('_d.')[0]
			maps.append(map_name)
		return maps

	def __getVMFObj(self, maps_dir, map_name):
		vmf_contents = self.vmf_parser.load("{}{}{}_d.vmf".format(maps_dir, os.sep, map_name))
		return vmf_contents

	def __getDimensionsOfMap(self, vmf_obj, scale_optimizer, method='solids'):
		"""
		Estimation function for determining the best boundries of a map. This takes into account a tournament stage and sky_box being baked into the same map.
		"""
		screenWidth = scale_optimizer[0]
		screenHeight = scale_optimizer[1]
		world_min = None # x,y,z
		world_max = None # x,y,z
		centerPos = {} # x, y, z
		scale = {'screenWidth' : screenWidth, 'screenHeight' : screenHeight, 'scale' : 0}

		plane_re = re.compile(r'\(([0-9\-\. ]+)\) \(([0-9\-\. ]+)\) \(([0-9\-\. ]+)\)')

		if method == 'solids':
			for solid in vmf_obj['world']['solid']:
				for side in solid['side']:
					if "plane" in side and ("material" not in side or ("toolsskybox" in side["material"])):
						result = plane_re.match(side["plane"])
						for plane_coord in [result.group(1), result.group(2), result.group(3)]:
							coords = plane_coord.split(" ")
							if world_min == None:
								world_min = [float(coords[0]), float(coords[1]), float(coords[2])]
								world_max = [float(coords[0]), float(coords[1]), float(coords[2])]
							else:
								world_min[0] = min(float(coords[0]), float(world_min[0]))
								world_min[1] = min(float(coords[1]), float(world_min[1]))
								world_min[2] = min(float(coords[2]), float(world_min[2]))
								world_max[0] = max(float(coords[0]), float(world_max[0]))
								world_max[1] = max(float(coords[1]), float(world_max[1]))
								world_max[2] = max(float(coords[2]), float(world_max[2]))
		elif method == 'entities':
			skybox_loc = self.__get3DSkyboxCoords(vmf_obj)
			compstage_loc = self.__getCompStageCoords(vmf_obj)

			for entity in vmf_obj['entity']:
				if "origin" in entity and ("targetname" not in entity or ("competitive" not in entity["targetname"])) and ("model" not in entity or ("skybox" not in entity["model"])) and ("targetname" not in entity or "skybox" not in entity["targetname"]) and ("classname" not in entity or ("sky_camera" not in entity["classname"])):
					coords = entity["origin"].split(" ")
					# Exclude the comp. stage at all times
					if self.__isEntityInBox((float(coords[0]), float(coords[1]), float(coords[2])), skybox_loc[0], skybox_loc[1]) == False and self.__isEntityInBox((float(coords[0]), float(coords[1]), float(coords[2])), compstage_loc[0], compstage_loc[1]) == False:
						if world_min == None:
							world_min = [float(coords[0]), float(coords[1]), float(coords[2])]
							world_max = [float(coords[0]), float(coords[1]), float(coords[2])]
						else:
							world_min[0] = min(float(coords[0]), float(world_min[0]))
							world_min[1] = min(float(coords[1]), float(world_min[1]))
							world_min[2] = min(float(coords[2]), float(world_min[2]))
							world_max[0] = max(float(coords[0]), float(world_max[0]))
							world_max[1] = max(float(coords[1]), float(world_max[1]))
							world_max[2] = max(float(coords[2]), float(world_max[2]))
		else:
			raise Exception('Unknown method used for determining dimensions.')

		scaleX = (abs(float(world_min[0])) + abs(float(world_max[0])))/screenWidth
		scaleY = (abs(float(world_min[1])) + abs(float(world_max[1])))/screenHeight

		if scaleX > scaleY:
			scale['scale'] = int(scaleX)+1
		else:
			scale['scale'] = int(scaleY)+1

		centerPos["x"] = ((abs(float(world_min[0])) + abs(float(world_max[0])))/2.0) + float(world_min[0])
		centerPos["y"] = ((abs(float(world_min[1])) + abs(float(world_max[1])))/2.0) + float(world_min[1])
		centerPos["z"] = float(world_max[2])

		return (world_min, world_max, scale, centerPos)

	def __get3DSkyboxCoords(self, vmf_obj):
		# get sky_camera and box around it
		camera = self.__getEntityCoordsByClassName(vmf_obj, 'sky_camera')
		# No camera, no 3d skybox
		if camera == None:
			return (None, None)
		else:
			world_min = [camera[0]-2000, camera[1]-2000, camera[2]-500]
			world_max = [camera[0]+2000, camera[1]+2000, camera[2]+500]
			return (world_min, world_max)

	def __getCompStageCoords(self, vmf_obj):
		# get competitive_stage and box around it
		stage = self.__getEntityCoordsByModelname(vmf_obj, 'competitive_stage')
		# Comp stage, no tournament stage present
		if stage == None:
			return (None, None)
		else:
			world_min = [stage[0]-1000, stage[1]-1000, stage[2]-500]
			world_max = [stage[0]+1000, stage[1]+1000, stage[2]+500]
			return (world_min, world_max)

	def __isEntityInBox(self, entity_coords, world_min, world_max):
		if world_min == None or world_max == None:
			return False
		if (entity_coords[0] >= world_min[0] and entity_coords[0] <= world_max[0]) and (entity_coords[1] >= world_min[1] and entity_coords[1] <= world_max[1]) and (entity_coords[2] >= world_min[2] and entity_coords[2] <= world_max[2]):
			return True
		else:
			return False

	def __getEntityCoordsByClassName(self, vmf_obj, class_name):
		for entity in vmf_obj['entity']:
			if "origin" in entity and "classname" in entity and entity["classname"] == class_name:
				coords = entity["origin"].split(" ")
				ret_coords = (float(coords[0]), float(coords[1]), float(coords[2]))
				return ret_coords
		return None

	def __getEntityCoordsByModelname(self, vmf_obj, model_name):
		for entity in vmf_obj['entity']:
			if "origin" in entity and "model" in entity and model_name in entity["model"]:
				coords = entity["origin"].split(" ")
				ret_coords = (float(coords[0]), float(coords[1]), float(coords[2]))
				return ret_coords
		return None

	def __getCameras(self, vmf_obj):
		cameras = []
		if type(vmf_obj['entity']) is list:
			for entity in vmf_obj['entity']:
				if 'classname' in entity and entity['classname'] == 'info_observer_point':
					cameras.append(entity)
		return cameras

	def __getMapVersion(self, vmf_obj):
		# "mapversion" "5483"
		if 'mapversion' in vmf_obj['world']:
			return int(vmf_obj['world']['mapversion'])
		else:
			return None

	def __md5(self, fname):
		hash_md5 = hashlib.md5()
		with open(fname, "rb") as f:
			for chunk in iter(lambda: f.read(4096), b""):
				hash_md5.update(chunk)
		return hash_md5.hexdigest()

	def __getHashForMap(self, maps_dir, map_name):
		file_hash = self.__md5("{}{}{}.bsp".format(maps_dir, os.sep, map_name))
		return file_hash

	def __getEntityCount(self, vmf_obj):
		return len(vmf_obj['entity'])

	def __getHealthKits(self, vmf_obj):
		return self.__getAllEntitiesByPartialClassName(vmf_obj, 'item_healthkit')

	def __getAmmoPacks(self, vmf_obj):
		return self.__getAllEntitiesByPartialClassName(vmf_obj, 'item_ammopack')

	def __getControlPoints(self, vmf_obj):
		return self.__getAllEntitiesByPartialClassName(vmf_obj, 'team_control_point')

	def __getBriefCases(self, vmf_obj):
		return self.__getAllEntitiesByPartialClassName(vmf_obj, 'item_teamflag')

	def __getSpawnPoints(self, vmf_obj):
		return self.__getAllEntitiesByPartialClassName(vmf_obj, 'info_player_teamspawn')

	def __getResupplyLockers(self, vmf_obj):
		return self.__getAllEntitiesByPartialModelName(vmf_obj, 'resupply_locker')

	def __containsHalloweenProps(self, vmf_obj):
		coords = self.__getEntityCoordsByModelname(vmf_obj, 'halloween')
		if coords is not None:
			return True
		return False

	def __getAllEntitiesByPartialClassName(self, vmf_obj, class_name):
		result = []
		for entity in vmf_obj['entity']:
			if "origin" in entity and "classname" in entity and class_name in entity["classname"]:
				result.append(entity)
		return result

	def __getAllEntitiesByPartialModelName(self, vmf_obj, model_name):
		result = []
		for entity in vmf_obj['entity']:
			if "origin" in entity and "model" in entity and model_name in entity["model"]:
				result.append(entity)
		return result

	def __saveMetadataToDisk(self, maps_metadata, metadata_output_filename):
		with open('.{}metadata{}{}'.format(os.sep, os.sep, metadata_output_filename), 'w') as outfile:
			json.dump(maps_metadata, outfile, sort_keys=True)


if __name__ == '__main__':
	# System specific settings
	# Make sure your path is set correct, and the BSPSource .jar is also in the same as this script.
	JAVA_EXEC = 'C:\\ProgramData\\Oracle\\Java\\javapath\\java.exe'
	MAPS_DIR = 'Z:\\TMP TF2 DUMP\\rc_tmp'
	OUTPUT_FILENAME = 'bsp_maps_metadata.json'
	# Main call
	gatherer = MapDataGatherer(JAVA_EXEC)
	gatherer.gatherMetadataFromBSPDir(maps_dir=MAPS_DIR, metadata_output_filename=OUTPUT_FILENAME)
