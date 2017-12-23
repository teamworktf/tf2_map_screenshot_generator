#!/usr/bin/python
# Created by Makamoto (teamwork.tf)
import time, json
import math, threading
import glob, gtk, re, wnck, gtk, os, pyautogui, psutil, subprocess
from pyautogui import press, typewrite, hotkey, keyDown, keyUp
import pyautogui
import numpy as np

class FatalGameCoordinatorException(Exception):
	pass

class GameCoordinator(object):
	"""
	GameCoordinator is a stateless utility object, which helps with communicting to the game.
	"""

	def __init__(self, game_base_dir, default_game_start_wait=40, default_map_switch_wait=25):
		"""
		Contructor
		"""
		self.game_p = None
		self.game_base_dir = game_base_dir
		self.maps_dir = '{}tf/maps/'.format(game_base_dir)
		self.default_game_start_wait = default_game_start_wait
		self.default_map_switch_wait = default_map_switch_wait

	def isTF2Running(self):
		return "hl2_linux" in (p.name() for p in psutil.process_iter())

	# WORKAROUND: Debian suspects TF2 of freezing during startup, this removes the notification.
	def clickGNOMEWaitProcess(self):
		pyautogui.click(x=1233, y=669)

	# Start the game
	def startupGame(self):
		# Open up TF2
		if self.isTF2Running() == True:
			raise FatalGameMapRunnerException("Team Fortress 2 is currently running.")
		print("Attempting to start game ...")
		self.game_p = subprocess.Popen([self.usr_steam_exec,'-applaunch', '440', 
										   '-nosound',
										   '-novid'
										   ],
									stdin=subprocess.PIPE,
									stdout=subprocess.PIPE,
									stderr=subprocess.PIPE)
		time.sleep(self.default_game_start_wait)
		# Click the wait button for GNOME process freeze
		self.clickGNOMEWaitProcess()
		time.sleep(15)
		if self.isTF2Running():
			print("Game is now started.")
		else:
			self.startupGame()
			return
		# Activate window
		screen = wnck.screen_get_default()
		titlePattern = re.compile('.*Team Fortress 2.*')
		windows = screen.get_windows()
		for w in windows:
			if titlePattern.match(w.get_name()):
				print("Activated window, waiting for input ...")
				w.activate(gtk.gdk.x11_get_server_time(gtk.gdk.get_default_root_window()))
		return

	def killGame(self):
		print("Attempting to kill the game ...")
		for proc in psutil.process_iter():
			if 'hl2_linux' in proc.name() :
				proc.kill()
				time.sleep(5)
				return

	def getAllMapsInTFFolder(self):
		maps = []
		full_path_maps = glob.glob("{}*.bsp".format(self.maps_dir))
		for full_path_map in full_path_maps:
			path_parts = full_path_map.split('/')
			map_name = path_parts[-1].split('.')[0]
			maps.append(map_name)
		return maps

	def getNotProcessedMapsInTFFolder(self):
		filtered_maps = []
		maps = getAllMapsInFolder()
		folders = [name for name in os.listdir(self.screenshots_storage_dir) if os.path.isdir("{}/{}".format(self.screenshots_storage_dir, name))]
		for map_name in maps:
			if map_name not in folders:
				filtered_maps.append(map_name)
		return filtered_maps

	def __sendCommand(cmd):
		typewrite("{}\n".format(cmd))
		time.sleep(0.5)

	def __openConsoleAndCmd(self, cmds):
		time.sleep(0.5)
		press('`')
		time.sleep(1)
		for cmd in cmds:
			self.__sendCommand(cmd)
		press('`')
		time.sleep(0.5)

	def changeMap(self, map_name):
		self.__openConsoleAndCmd(['map {}'.format(map_name)])
		time.sleep(self.default_map_switch_wait)
		print("Loaded map {}".format(map_name))
		return

	def clickScreen():
		pyautogui.click(x=1233, y=669)

	def isMapLoaded(self):
		if self.isTF2Running() == False:
			return False
		# check with an image if we're not in the game menu yet
		menu_check = pyautogui.locateOnScreen('menu_find_game.png')
		if menu_check == None:
			return True
		else:
			return False
	
	def prepareMapForScreenshots(self,  map_name):
		# Go through welcome screen
		# Select spectator
		if 'mvm_' in map_name:
			for x in range(0,1):
				pyautogui.click(x=1651, y=1025)
				time.sleep(0.5)
			press('1')
			openConsoleAndCmd(['spectate'])
			self.clickScreen()
		else:
			for x in range(0,4):
				pyautogui.click(x=1651, y=1025)
				time.sleep(0.5)
			press('2')
		time.sleep(0.5)
		# Trigger noclip in firstperson (recommended)
		self.__openConsoleAndCmd(['sv_cheats 1', 'r_drawviewmodel 0', 'cl_drawhud 0', 'noclip', 'mat_picmip -1', 'r_lod 0', 'mat_fullbright 0'])
		# Triggering noclip requires pressing space twice
		time.sleep(2)
		press('space')
		time.sleep(0.5)
		press('space')
		time.sleep(0.5)

	def prepareForSpectatorScreenshots(self):
		self.__openConsoleAndCmd(['spectate'])

	def prepareForBoxScreenshots(self):
		pass

	def prepareForOverviewScreenshots(self):
		self.__openConsoleAndCmd(['fog_enable 0', 'fog_override 1', 'r_portalsopenall 1'])

	def setCorrectOverview(self, pos, ypos, scale):
		self.__openConsoleAndCmd(['setpos_exact {} {} {}'.format(pos["x"], pos["y"], ypos), 'cl_leveloverview {}'.format(scale)])

	def prepareMapForUnload(self, map_name):
		self.__openConsoleAndCmd(['cl_leveloverview 0', 'cl_drawhud 1', 'noclip'])

