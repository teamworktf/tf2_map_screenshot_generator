#!/usr/bin/python
# Created by Makamoto (teamwork.tf)
import re

class VMFParser(object):
	"""
	Stateless VMF (Valve Map Format) Parser for Python.
	"""

	def __init__(self):
		"""
		Contructor
		"""
		self.vmf_re = re.compile('"([^"]*?)" "([^"]*?)"')

	def load(self, vmf_obj_location):
		"""
		Load an object from the filesystem.
		"""
		if type(vmf_obj_location) is not str:
			raise Exception('Must supply the VMF file location in a str.')

		with open(vmf_obj_location) as data_file:
			vmf_contents = data_file.read()	

		lines = vmf_contents.split('\n')
		obj = self.__parseLinesPerObj(lines)
		return obj

	def __parseLinesPerObj(self, lines, i=0):
		obj = {}
		while i < len(lines):
			line = lines[i].strip()
			if line == '':
				pass
			elif line[0] == '"':
				# A var
				result = self.vmf_re.match(line)
				obj[result.group(1)] = result.group(2)
			elif line[0] == '{' or line[0] == '}':
				# Opening bracket already came with object name
				# Closing bracket means end of this object
				if line[0] == '}':
					return (obj, i)
			else:
				# Obj in this obj
				if line in obj:
					# Check if it's already a list
					if type(obj[line]) is not list:
						tmp_obj = obj[line]
						obj[line] = [tmp_obj]
					(new_obj, i) = self.__parseLinesPerObj(lines, i+1)
					obj[line].append(new_obj)
				else:
					# Parse object
					(obj[line], i) = self.__parseLinesPerObj(lines, i+1)
			i += 1
		return obj

	def save(obj):
		"""
		Save an VMF object to the filesystem.
		"""
		raise NotImplementedError()