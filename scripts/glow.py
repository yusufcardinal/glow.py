"""
Glow.py v0.1 Public Release

Creator: Mile
Huge thanks to FerrariFlunker, Bytebit and BR for their invaluable help!

COPY THIS TO YOUR map.txt FILE FOR MAP-SPECIFIC CONTROL AND ENABLE GLOW ON THE MAP

extensions = {
    'glow_enabled': True,
    'glow_global_multiplier': (255, 255, 255)
    'stored_colors': {}
}

THIS SCRIPT RELIES ON 'detectclient.py' IN ORDER TO DEACTIVATE GLOW FEATURES FOR VOXLAP USERS. PLEASE MAKE SURE
'detectclient.py' IS ALSO RUNNING ON YOUR SERVER!

"""

import math
from twisted.internet import reactor
from pyspades.contained import BlockAction, SetColor
from pyspades.server import block_action
from pyspades.common import Vertex3
from pyspades.constants import *
from pyspades.common import make_color
from pyspades.server import set_color
from commands import add, alias, get_player, name, admin

# USER INPUTS

# NUMBER OF GLOW BLOCKS ON SPAWN

INVENTORY_SIZE = 50

# GLOBAL MULTIPLIERS
# Regardless of lit block's colors, it will be multiplied by this color. Use this if you want to shift all lights
# towards a certain hue. Put all values at 255 to toggle off. Can also be changed in map.txt by changing
# 'glow_global_multiplier'.

USER_R = 255.0
USER_G = 255.0
USER_B = 255.0

# ANTI LAG LINE
# Creating lines of light blocks may cause a lot of server-side lag, especially with a full server. ANTI_LAG_LIMIT is
# the maximum amount of blocks that can light up in a line when ANTI_LAG_LINE is on. Change ANTI_LAG_LINE to False to
# turn off. Players in god mode can place as many light blocks as they want at once, regardless of these settings.

ANTI_LAG_LINE = True
ANTI_LAG_LIMIT = 5


# PALETTE TOGGLE
# This turns off colors from the color palette so they may not glow. The script makes it so about half the color palette
# glows by default, this reduces the number of glowy blocks to the three lightest columns of player palette.
PALETTE_TOGGLE = True
PALETTE_PLAYER = list([(255, 31, 31), (255, 143, 31), (255, 255, 31), (31, 255, 31), (31, 255, 255), (31, 31, 255), (255, 31, 255)])

# END OF USER INPUTS

# Colors saved from the map.
STORED_COLORS = {
}

# Variables driving the stacking of glows. (WIPPPP)
STORED_LITNESS = {
}

MAP_IS_GLOW = False

# Block placed when inventory reaches zero


def empty_lights(protocol, self, a, b, c, map):
	re, ge, be = map.get_color(a, b, c)
	RGB = (re/2, ge/2, be/2)
	set_color = SetColor()
	set_color.value = make_color(re/2, ge/2, be/2)
	set_color.player_id = self.player_id
	protocol.send_contained(set_color)
	block_action.player_id = 33
	map.set_point(a, b, c, RGB)
	block_action.x = a
	block_action.y = b
	block_action.z = c
	block_action.value = BUILD_BLOCK
	# Send block updates to everyone but voxlap and turned off users
	protocol.send_contained(block_action, save=True, rule=lambda p: p.is_glow is True)


def glow_block_user(protocol, self, a, b, c, value, tolerance, map):

	R1, G1, B1 = map.get_color(a, b, c)
	voxel_selection_user = list()
	toleranceVal = 1

	for ac in range(a-tolerance, a+tolerance):
		for bc in range(b-tolerance, b+tolerance):
			for cc in range(c-tolerance, c+tolerance):
				if map.get_solid(ac, bc, cc):
					if R1 == map.get_color(ac, bc, cc)[0] and \
							G1 == map.get_color(ac, bc, cc)[1] and \
							B1 == map.get_color(ac, bc, cc)[2]:
						toleranceVal += 2

	for a2 in range(a-value, a+value):
		for b2 in range(b-value, b+value):
			for c2 in range(c-value, c+value):
				result = tuple((a2, b2, c2))
				voxel_selection_user.append(result)
	for p in voxel_selection_user:
		if map.get_solid(p[0], p[1], p[2]):
			R2, G2, B2 = map.get_color(p[0], p[1], p[2])
			distance = math.sqrt((p[0] - a) ** 2 + (p[1] - b) ** 2 + (p[2] - c) ** 2)
			if distance > value:
				continue
			if R2 == 0 and G2 == 0 and B2 == 0:
				continue
			else:
				if p not in STORED_COLORS:
					STORED_COLORS[p] = tuple((R2, G2, B2))
				value = float(value)
				R1, G1, B1, R2, G2, B2 = float(R1), float(G1), float(B1), float(R2), float(G2), float(B2)
				R3 = int(R2 + ((R1 / 255) * USER_R - ((distance / value) * ((R1/255)*USER_R))) / toleranceVal)
				G3 = int(G2 + ((G1 / 255) * USER_G - ((distance / value) * ((G1/255)*USER_G))) / toleranceVal)
				B3 = int(B2 + ((B1 / 255) * USER_B - ((distance / value) * ((B1/255)*USER_B))) / toleranceVal)
				if R3 > 254:
					R3 = 254
				if G3 > 254:
					G3 = 254
				if B3 > 254:
					B3 = 254
				if R3 < 0:
					R3 = 0
				if G3 < 0:
					G3 = 0
				if B3 < 0:
					B3 = 0
				RGB = (R3, G3, B3)
				if R2 < 255 and G2 < 255 and B2 < 255:
					set_color = SetColor()
					set_color.value = make_color(R3, G3, B3)
					set_color.player_id = 33
					protocol.send_contained(set_color)
					block_action.player_id = 33
					map.set_point(p[0], p[1], p[2], RGB)
					block_action.x = p[0]
					block_action.y = p[1]
					block_action.z = p[2]
					block_action.value = BUILD_BLOCK
					# Send block updates to everyone but voxlap and turned off users
					protocol.send_contained(block_action, save=True, rule=lambda p: p.is_glow is True)


def unglow_block_user(protocol, self, a, b, c, value, tolerance, map):

	R1, G1, B1 = map.get_color(a, b, c)
	voxel_selection_user = list()
	toleranceVal = 1

	for ac in range(a-tolerance, a+tolerance):
		for bc in range(b-tolerance, b+tolerance):
			for cc in range(c-tolerance, c+tolerance):
				if map.get_solid(ac, bc, cc):
					if R1 == map.get_color(ac, bc, cc)[0] and \
							G1 == map.get_color(ac, bc, cc)[1] and \
							B1 == map.get_color(ac, bc, cc)[2]:
						toleranceVal += 2

	for a2 in range(a-value, a+value):
		for b2 in range(b-value, b+value):
			for c2 in range(c-value, c+value):
				result = tuple((a2, b2, c2))
				voxel_selection_user.append(result)
	for p in voxel_selection_user:
		if map.get_solid(p[0], p[1], p[2]):
			R2, G2, B2 = map.get_color(p[0], p[1], p[2])
			distance = math.sqrt((p[0] - a) ** 2 + (p[1] - b) ** 2 + (p[2] - c) ** 2)
			if distance > value:
				continue
			if R2 == 0 and G2 == 0 and B2 == 0:
				continue
			else:
				value = float(value)
				R1, G1, B1, R2, G2, B2 = float(R1), float(G1), float(B1), float(R2), float(G2), float(B2)
				R3 = int(R2 - ((R1/255)*USER_R-((distance/value)*((R1/255)*USER_R)))/toleranceVal - 1)
				G3 = int(G2 - ((G1/255)*USER_G-((distance/value)*((G1/255)*USER_G)))/toleranceVal - 1)
				B3 = int(B2 - ((B1/255)*USER_B-((distance/value)*((B1/255)*USER_B)))/toleranceVal - 1)
				if R3 > 254:
					R3 = 254
				if G3 > 254:
					G3 = 254
				if B3 > 254:
					B3 = 254
				if R3 < 0:
					R3 = 0
				if G3 < 0:
					G3 = 0
				if B3 < 0:
					B3 = 0
				if p in STORED_COLORS:
					if R3 < STORED_COLORS[p][0]:
						R3 = STORED_COLORS[p][0]
					if G3 < STORED_COLORS[p][1]:
						G3 = STORED_COLORS[p][1]
					if B3 < STORED_COLORS[p][2]:
						B3 = STORED_COLORS[p][2]
				RGB = (R3, G3, B3)
				if R2 < 255 and G2 < 255 and B2 < 255:
					set_color = SetColor()
					set_color.value = make_color(R3, G3, B3)
					set_color.player_id = 33
					protocol.send_contained(set_color)
					block_action.player_id = 33
					map.set_point(p[0], p[1], p[2], RGB)
					block_action.x = p[0]
					block_action.y = p[1]
					block_action.z = p[2]
					block_action.value = BUILD_BLOCK
					# Send block updates to everyone but voxlap and turned off users
					protocol.send_contained(block_action, save=True, rule=lambda p: p.is_glow is True)

@alias('glow')
def off_glow(self):
	if self.client_info.client != ord('a'):
		if self.is_glow:
			self.is_glow = False
			self.send_chat("Glow turned OFF.")
		else:
			self.is_glow = True
			self.send_chat("Glow turned ON.")
	else:
		self.send_chat("Cannot run glow on classic client. Please upgrade to OpenSpades or BetterSpades.")
add(off_glow)

@alias('glowmap')
def force_glow(self):
	global MAP_IS_GLOW
	if self.user_types.moderator or self.admin:
		if MAP_IS_GLOW:
			MAP_IS_GLOW = False
			self.send_chat("Glow turned OFF globally.")
		else:
			MAP_IS_GLOW = True
			self.send_chat("Glow turned ON globally.")
	else:
		self.send_chat("Permission denied.")
add(force_glow)


def apply_script(protocol, connection, config):

	class GlowProtocol(protocol):
		def __init__(self, *arg, **kw):
			protocol.__init__(self, *arg, **kw)
#			reactor.addSystemEventTrigger('before', 'shutdown', self.save_storedcolor)

#		def save_storedcolor(self):
#			with open('STORED_COLOR.txt', 'w') as file:
#				file.write(str(STORED_COLORS))

		def on_map_change(self, map):
			global MAP_IS_GLOW, USER_R, USER_G, USER_B, STORED_COLORS
			extensions = self.map_info.extensions
			if extensions.has_key('glow_enabled'):
				MAP_IS_GLOW = extensions['glow_enabled']
			else:
				MAP_IS_GLOW = False
			if extensions.has_key('glow_global_multiplier'):
				USER_R = extensions['glow_global_multiplier'][0]
				USER_G = extensions['glow_global_multiplier'][1]
				USER_B = extensions['glow_global_multiplier'][2]
			if extensions.has_key('glow_stored_colors'):
				STORED_COLORS = extensions['glow_stored_colors']
			return protocol.on_map_change(self, map)

	class GlowConnection(connection):

		def __init__(self, *args, **kwargs):
			connection.__init__(self, *args, **kwargs)
			self.light_amount = INVENTORY_SIZE
			self.is_glow = True

		def on_spawn(self, pos):
			if self.client_info.client == ord('a'):
				self.is_glow = False
			return connection.on_spawn(self, pos)

		def on_block_build(self, a, b, c):
			if MAP_IS_GLOW:
				map = self.protocol.map
				protocol = self.protocol
				color = map.get_color(a, b, c)
				p2 = tuple((a, b, c))
				if p2 not in STORED_COLORS:
					STORED_COLORS[p2] = color
				if PALETTE_TOGGLE and color in PALETTE_PLAYER:
					return connection.on_block_build(self, a, b, c)
				else:
					if color[0] == 255 or color[1] == 255 or color[2] == 255:
						if self.light_amount <= 0 and not self.god:
							if self.is_glow:
								self.send_chat("You\'ve run out of light blocks! Go to your tent to refill.")
							empty_lights(protocol, self, a, b, c, map)
						else:
							glow_block_user(protocol, self, a, b, c, 7, 3, map)
							self.light_amount -= 1
							if self.is_glow:
								self.send_chat(str(self.light_amount) + " light blocks remaining.")
			else:
				#Map isn't glow enabled
				return connection.on_block_build(self, a, b, c)

			return connection.on_block_build(self, a, b, c)

		def on_block_destroy(self, a, b, c, mode):
			if MAP_IS_GLOW:
				map = self.protocol.map
				protocol = self.protocol
				color = map.get_color(a, b, c)
				p2 = tuple((a, b, c))
				if p2 in STORED_COLORS:
					del STORED_COLORS[p2]
				if PALETTE_TOGGLE and color in PALETTE_PLAYER:
					return connection.on_block_destroy(self, a, b, c, mode)
				else:
					if mode != GRENADE_DESTROY:
						if color[0] == 255 or color[1] == 255 or color[2] == 255:
							unglow_block_user(protocol, self, a, b, c, 7, 3, map)
							if self.light_amount < INVENTORY_SIZE:
								self.light_amount += 1
							if self.is_glow:
								self.send_chat(str(self.light_amount) + " light blocks remaining.")
			else:
				#Map isn't glow enabled
				return connection.on_block_destroy(self, a, b, c, mode)
			return connection.on_block_destroy(self, a, b, c, mode)

		def on_line_build(self, points):

			if MAP_IS_GLOW:
				map = self.protocol.map
				protocol = self.protocol
				color = map.get_color(points[0][0], points[0][1], points[0][2])
				if PALETTE_TOGGLE and color in PALETTE_PLAYER:
					return connection.on_line_build(self, points)
				else:
					if len(points) > ANTI_LAG_LIMIT and ANTI_LAG_LINE is True and not self.god:
						if color[0] == 255 or color[1] == 255 or color[2] == 255:
							for a, b, c in points:
								empty_lights(protocol, self, a, b, c, map)
								p2 = tuple((a, b, c))
								if p2 not in STORED_COLORS:
									STORED_COLORS[p2] = map.get_color(a, b, c)
							if self.is_glow:
								self.send_chat("Maximum allowed light blocks at a time is " + str(ANTI_LAG_LIMIT) + ".")
						else:
							for a, b, c in points:
								p2 = tuple((a, b, c))
								if p2 not in STORED_COLORS:
									STORED_COLORS[p2] = color

							return connection.on_line_build(self, points)
					else:
						for a, b, c in points:
							p2 = tuple((a, b, c))
							if p2 not in STORED_COLORS:
								STORED_COLORS[p2] = color
							if color[0] == 255 or color[1] == 255 or color[2] == 255:
								if self.light_amount <= 0 and not self.god:
									if self.is_glow:
										self.send_chat("You\'ve run out of light blocks! Go to your tent to refill.")
									empty_lights(protocol, self, a, b, c, map)
								else:
									glow_block_user(protocol, self, a, b, c, 7, 3, map)
									self.light_amount -= 1
									if self.is_glow:
										self.send_chat(str(self.light_amount) + " light blocks remaining.")
			else:
				# Map isn't glow enabled
				return connection.on_line_build(self, points)

			return connection.on_line_build(self, points)

		def on_refill(self):
			if MAP_IS_GLOW:
				self.light_amount = INVENTORY_SIZE
				if self.is_glow:
					self.send_chat("Light blocks refilled!")
			else:
				return connection.on_refill(self)
			return connection.on_refill(self)

		def on_kill(self, killer, type, grenade):
			self.light_amount = INVENTORY_SIZE
			return connection.on_kill(self, killer, type, grenade)

	return GlowProtocol, GlowConnection
