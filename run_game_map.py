#!/usr/bin/python
# Created by Makamoto (teamwork.tf)
import time, json
import math, threading
import glob, gtk, re, wnck, gtk, os, pyautogui, psutil, subprocess
from pyautogui import press, typewrite, hotkey, keyDown, keyUp
import pyautogui
import numpy as np
from PIL import Image
import subprocess
import game_coordinator

class FatalGameMapRunnerException(Exception):
	pass

class GameMapRunner(object):
	"""
	GameMapRunner is a statefull utility object, which runs TF2 to gather screenshots from the game, with the use of metadata provided by the gatherer.
	
	Currently only Linux Compatible (tested on Debian Jessie), optimized for 1920x1080 ONLY. Will not work with other resolutions, unless edited.

	Required installs:
	- Team Fortress 2
	- pyautogui, numpy, PIL (use PIP to install these)
	"""

	"""
	There are 3 available taks to execute per map:
	Tasks {1,2} are the least intensive and thus the fastest to execute. These create screenshots of all the spectator cams and leveloverview.
	Task 3 creates screenshots of every spectator place and tries to stictch them together. This is far from perfect.
	"""
	TASK_SPECTATOR_CAMS 	= 1
	TASK_LEVELOVERVIEW 		= 2
	TASK_360_IMAGES 		= 3
	TASK_ISOMETRIC_CAMS 	= 4

	def __init__(self, game_base_dir, screenshots_storage_dir, metadata_filename, max_360_spec_cams=2, post_process=True, delete_leftover_images=True, pp_stitch_folder=None, pp_stitch_exec=None):
		"""
		Contructor
		"""
		self.usr_steam_exec = '/usr/bin/steam'
		self.maps_dir = '{}tf/maps/'.format(game_base_dir)
		self.screenshots_storage_dir = screenshots_storage_dir
		self.gc = game_coordinator.GameCoordinator(game_base_dir=game_base_dir)
		self.max_360_spec_cams = max_360_spec_cams
		self.post_process = post_process
		self.delete_leftover_images = delete_leftover_images
		self.pp_stitch_folder = pp_stitch_folder
		self.pp_stitch_exec = pp_stitch_exec
		with open(metadata_filename) as data_file:
			self.metadata = json.loads(data_file.read())

	def __getMapMetadata(self, map_name):
		return self.metadata[map_name]

	def __saveMetadataToFolder(self, map_name):
		metadata = self.__getMapMetadata(map_name)
		if metadata is not None:
			with open('{}/{}/metadata.json'.format(self.screenshots_storage_dir, map_name), 'w') as outfile:
				json.dump(metadata, outfile)

	# Stub, currently unused.
	def __prepareForGame(self):
		return
		
	def gatherScreenshotsBasedOnMetadata(self, metadata_filename, tasks):
		self.__verifyUserCorrectSetup()
		self.gc.startupGame()
		self.__prepareForGame()
		i = 0
		maps = self.gc.getNotProcessedMapsInTFFolder()
		for map_name in maps:
			metadata = self.__getMapMetadata(map_name)
			if metadata == None:
				print("Found a gamemap called '{}', but did not found metadata for this map, skipping this map.".format(map_name))
			else:
				print("Now starting to process map '{}' ({}/{})".format(map_name, i, len(maps)))
				self.gc.changeMap(map_name)
				if self.gc.isMapLoaded() == True:
					self.gc.prepareMapForScreenshots(map_name)
					# Execute the actual tasks
					# Tasks with spectator cams
					if GameMapRunner.TASK_SPECTATOR_CAMS in tasks:
						take360 = False
						if GameMapRunner.TASK_360_IMAGES in tasks:
							take360 = True
						self.__generateSpectatorScreenshotsForMaps(map_name, take360=take360)

					# Generate a leveloverview.
					if GameMapRunner.TASK_LEVELOVERVIEW in tasks:
						self.__generateOverviewScreenshotsForMaps(map_name)

					# Generate automatic Isometric images of the map.
					if GameMapRunner.TASK_ISOMETRIC_CAMS in tasks:
						raise FatalGameMapRunnerException("Task TASK_ISOMETRIC_CAMS not implemented yet.")


					self.gc.prepareMapForUnload(map_name)
					self.__saveMetadataToFolder(map_name)
					time.sleep(1)
				else:
					print("Map '{}' could not be loaded.".format(map_name))
					self.gc.killGame()
					self.gc.startupGame()
					self.__prepareForGame()
			i += 1
		self.gc.killGame()
		self.__printFinished()

	def __makeScreenshot(self, map_name, name):
		dir_check = '{}/{}/'.format(self.screenshots_storage_dir, map_name)
		if not os.path.exists(dir_check):
			os.makedirs(dir_check)
		pyautogui.screenshot('{}/{}/{}.png'.format(self.screenshots_storage_dir, map_name, name))
		time.sleep(1)
		print("Made screenshot '{}' for '{}'.".format(name, map_name))
		return

	def __generateSpectatorScreenshotsForMaps(self, map_name, take360):
		self.gc.prepareForSpectatorScreenshots()
		# Loop through spectator cams
		metadata = self.__getMapMetadata(map_name)
		for x in range(0, len(metadata['cameras'])):
			self.__makeScreenshot(map_name, '{}_{}'.format('spectator', x))
			time.sleep(1)

			if take360 == True and x < self.max_360_spec_cams:
				self.__generateBoxScreenshotsForMaps(map_name, spec_cam=x)
				time.sleep(1)
			self.gc.clickScreen()
			time.sleep(1.2)

	def __makeBoxScreenshotAndSave(self, map_name, image_name, setang_args):
		self.gc.openConsoleAndCmd(['setang_exact {}'.format(setang_args)])
		self.__makeScreenshot(map_name, image_name)

	def __generateBoxScreenshotsForMaps(self, map_name, spec_cam):
		self.gc.prepareForBoxScreenshots()
		images = []
		# MOST COMPLETE OF IMAGES, BUT SLOW
		# for x in [0, 45, 90, 135, 180, 225, 270, 315]:
		# 	for y in [-60, -30, 0, 30, 60]:
		# Loop through every x,y
		for x in [0, 90, 180, 270]:
			for y in [-60, -30, 0, 30, 60]:
				image_name = '{}_{}_{}_{}'.format('box', spec_cam, x, y)
				images.append(image_name)
				self.__makeBoxScreenshotAndSave(map_name, image_name, '{} {} 0'.format(y, x))

		# Bottom / top
		image_name = '{}_{}_bottom'.format('box', spec_cam)
		images.append(image_name)
		self.__makeBoxScreenshotAndSave(map_name, image_name, '90 0 0'.format(y, x))

		image_name = '{}_{}_top'.format('box', spec_cam)
		images.append(image_name)
		self.__makeBoxScreenshotAndSave(map_name, image_name, '-90 0 0'.format(y, x))

		if self.post_process == True:
			t = threading.Thread(target=stitch360Image, args=[map_name, images, spec_cam])
			t.start()

	def stitch360Image(self, map_name, images, spec_cam):
		if self.pp_stitch_exec == None:
			print("Skipping the 360 image stitching, as no Exec has been set.")
			return
		cwd = os.getcwd()
		os.chdir(self.pp_stitch_folder)

		output_filename = '{}/{}/360_spec{}.jpg'.format(self.screenshots_storage_dir, map_name, spec_cam)

		cmd = ['primusrun', self.pp_stitch_exec, '-GPU', 'Default', output_filename]
		cmd_args = []
		for image in images:
			cmd_args.append('{}/{}/{}.png'.format(self.screenshots_storage_dir, map_name, image))
		cmd.extend(cmd_args)

		print(' '.join(cmd))

		process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		output, error = process.communicate()
		print(output)

		# Check if the output is more than just one pixel
		if os.path.getsize(output_filename) < 1024:
			os.remove(output_filename)
		os.chdir(cwd)

		if self.delete_leftover_images == True:
			for image in images:
				filename = '{}/{}/{}.png'.format(self.screenshots_storage_dir, map_name, image)
				os.remove(filename)

	def __generateOverviewScreenshotsForMaps(map_name):
		self.gc.prepareForOverviewScreenshots()
		metadata = self.__getMapMetadata(map_name)

		pos = metadata['dimensions'][3]
		scale = metadata['dimensions'][2]['scale']
		i = 0
		for y in [-1500, -1000, 0, 400, 900]:
			ypos = pos["z"]+y
			if ypos < 0:
				ypos = 0
			this.gc.setCorrectOverview(pos, ypos, scale)
			this.__makeScreenshot(map_name, '{}_{}'.format('overview', i))
			i += 1

		if self.post_process == True:
			this.__mergeOverviewScreenshots(map_name)

	def __mergeOverviewScreenshots(self, map_name):
		full_path_overviews = sorted(glob.glob('{}/{}/overview_*.png'.format(self.screenshots_storage_dir, map_name)))
		overviews_to_merge = []

		# Make the images transparant and elect the best images
		# This is required to prevent green screenshots from merging into the image
		# However, make sure at least 0..Z_POS_CENTER+1 is being used, Z_POS_CENTER = 3
		i = 0
		for overview_image in full_path_overviews:
			top_left_pixel = self.__convertImageToTopLeftPixelTransparency(overview_image)
			if (top_left_pixel[0] == 0 and top_left_pixel[1] == 0 and top_left_pixel[2] == 0) or (i < 3):
				overviews_to_merge.append(overview_image)
			i += 1

		# Merge layers
		background = Image.open(full_path_overviews[0])
		for overview_image in overviews_to_merge:
			if overview_image is not full_path_overviews[0]:
				overlay = Image.open(overview_image)
				background.paste(overlay, (0, 0))
			
		background.save('{}/{}/overview_merged.png'.format(self.screenshots_storage_dir, map_name), "PNG")

		if self.delete_leftover_images == True:
			for overview_image in full_path_overviews:
				if 'overview_merged' not in overview_image:
					os.remove(overview_image)

	def __convertImageToTopLeftPixelTransparency(self, image_path):
		img = Image.open(image_path)
		img = img.convert("RGBA")
		datas = img.getdata()

		newData = []
		top_left_pixel = datas[0]
		for item in datas:
			# Remove green anti-aliasing
			if item[0] == 39 and item[1] == 190 and item[2] == 36:
				newData.append((0, 0, 0, 0))
			elif item[0] == top_left_pixel[0] and item[1] == top_left_pixel[1] and item[2] == top_left_pixel[2]:
				newData.append((0, 0, 0, 0))
			else:
				newData.append(item)

		img.putdata(newData)
		img.save(image_path, "PNG")
		return newData[0]

	def __verifyUserCorrectSetup(self):
		print("="*100)
		print("- Make sure the .bsp files are placed in the TF2 maps folder (location: {}).".format(self.maps_dir))
		print("- Make sure you enabled the console in the game.")
		print("- Make sure you closed the game.")
		print("="*100)
		raw_input("Press any key to continue ...")

	def __printFinished(self):
		print("="*100)
		print("Finished processing all maps in the queue.")
		print("="*100)



if __name__ == '__main__':
	# System specific settings
	METADATA_FILENAME = './metadata/bsp_maps_metadata_community3.json'
	tasks = [GameMapRunner.TASK_SPECTATOR_CAMS, GameMapRunner.TASK_LEVELOVERVIEW]
	game_base_dir = '/home/sander/.local/share/Steam/steamapps/common/Team Fortress 2/'
	screenshots_storage_dir = '/home/sander/tf2/screenshots'
	# Main call
	runner = GameMapRunner()
	runner.gatherScreenshotsBasedOnMetadata(metadata_filename=METADATA_FILENAME, tasks=tasks, game_base_dir=game_base_dir, screenshots_storage_dir=screenshots_storage_dir)
