#!/usr/bin/python3
import re

class MapStatsCoordinator(object):
	"""
	Stub class for the Map Statistics Coordinator from teamwork.tf. This only contains the functions required by the BSP metadata info gathering, and not the other methods defined for the website.
	"""

	def __init__(self):
		"""
		Contructor
		"""
		self.re_map_name_normalizer = re.compile(r'\_((test|a[0-9]*|b[0-9]*|alpha[0-9]*|beta[0-9]*|ab[0-9]*|r[0-9]*|r[0-9]+[a-z\-]*|rc[0-9]*|rc[0-9]+[a-z\-]*|v[0-9]*|ver[0-9]+|v[0-9]+[a-z\-]*|remix[0-9]*|final[0-9]*|all|fixed[0-9]*|fix[0-9]*|normal[0-9]*|intermediate[0-9]*|advanced[0-9]*|adv[0-9]*|expert[0-9]*|[0-9]+|reloaded)([ab]{0,1}[0-9]{0,1}))($|\_)', re.M|re.I)

	def helperNormalizeMapName(self, name):
		if name == None:
			return None

		match = re.search(self.re_map_name_normalizer, name)
		normalized_to_end_name = name
		if match is not None and match.group(0) != None:
			new_proposal = normalized_to_end_name.split(match.group(0))[0]
			if len(new_proposal) > 3:
				normalized_to_end_name = new_proposal
			else:
				# check of things like: cp_final_cool_b1
				name_parts = name.split("_")
				new_proposal_parts = name_parts
				for i, part in reversed(list(enumerate(name_parts))):
					match = re.search(COMPILED_REGEX_MAP_NAME, "_{}".format(part))
					if match is not None and match.group(0) != None and len('_'.join(name_parts[0:i])) > 3:
						del new_proposal_parts[i]
					elif len('_'.join(name_parts[0:i])) <= 3:
						break;

				normalized_to_end_name = '_'.join(new_proposal_parts)
		
		return normalized_to_end_name
