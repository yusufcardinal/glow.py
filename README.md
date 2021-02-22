# glow.py
A very crude and poorly-written point light system implementation for Pysnip

Thank you to Dr.Morphman and a_girl for texture.py (https://www.buildandshoot.com/forums/viewtopic.php?t=11173) , which inspired me to eventually write this.

# How does it work?
glow simply simulates a point light whenever a block has any of its RGB values equal to 255. The lights are additive to one-another, and the effect disappears once the blocks are removed. By default the plugin is turned off on all maps and needs to be forced in map.txt

# Is it easy to run?
Running the plugin in an appropriate manner requires a bit of preparation, that I will develop on further in this readme later on. In the meantime, you can read the insutrctions at the top of glow.py and refer to the example maps provided.
