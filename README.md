# Automatic image generator for Source Engine gamemaps (TF2)

This repository contains the tools used to generate a set of spectator images and level overview for every gamemap within TF2. It consists of two stages; the retrieval of the neccesary information from the .bsp files, and running the game to take the actual screenshots. The current dev gameshots system within TF2 is currently not sufficient for almost all gamemaps.

## Metadata extractor for Source Engine gamemaps

This metadata extractor accepts an folder with `.bsp` files and outputs a `.json` file containing all the extracted metadata for the maps that were processed.

Tested almost all TF2 maps available for download on the internet. It is combined with the minimal stubs VMF_Parser and MapStatsCoordinator from teamwork.tf to make this work.

## Dependencies
This metadata extractor relies on an external dependency called BSPSource. You need to make sure this is present on the same machine to make the data extraction work:
* Windows machine
* Java (JDK 1.6 or higher)
* [BSPSource](https://developer.valvesoftware.com/wiki/BSPSource) downloaded and placed inside the same folder.
* VMF_Parser in Python (included in the repository).


## Example of the output

The output is a dictionary with every map name as  an entry, with the metadata as the result.

```json
"cp_glassworks_rc6a": {
"ammoPacks": [{"AutoMaterialize": "1", "StartDisabled": "0", "TeamNum": "0", "angles": "0 0 0", "classname": "item_ammopack_small", "fademindist": "-1", "id": "7817", "origin": "-3976 800 17"} ... ], 
"briefCases": [], 
"cameras": [{"StartDisabled": "0", "TeamNum": "0", "angles": "11 144 0", "associated_team_entity": "cp_red2", "classname": "info_observer_point", "defaultwelcome": "0", "fov": "0", "id": "753422", "origin": "-1600 1152 324"} ...], 
"containsHalloweenProps": false, 
"controlPoints": [{"classname": "team_control_point_master", "custom_position_x": "-1", "custom_position_y": "-1", "id": "6775", "origin": "160 -16 128.004", "targetname": "5cp_master", "team_base_icon_2": "sprites/obj_icons/icon_base_red", "team_base_icon_3": "sprites/obj_icons/icon_base_blu"} ...], 
"dimensions": [[-5466.0, -4475.0, -744.0], [5466.0, 4338.0, 1428.0], {"scale": 9, "screenHeight": 1080, "screenWidth": 1920}, {"x": 0.0, "y": -68.5, "z": 1428.0}], 
"entityCount": 3756, 
"fileHash": "9f169ea81bc9a1b2c6d4f5f0bdbde7d0", 
"healthKits": [{"AutoMaterialize": "1", "StartDisabled": "0", "TeamNum": "0", "angles": "0 0 0", "classname": "item_healthkit_small", "fademindist": "-1", "id": "7821", "origin": "-4024 800 17"} ...], 
"normalizedMapName": "cp_glassworks", 
"resupplyLockers": [5270.41, -897.867, 8.16007], 
"skyboxCamera": {"angles": "0 0 0", "classname": "sky_camera", "fogblend": "0", "fogcolor": "113 115 142", "fogcolor2": "255 255 255", "fogdir": "1 0 0", "fogenable": "1", "fogend": "8000", "fogmaxdensity": ".9", "fogstart": "100", "id": "1016124", "origin": "88 9672 427.5", "scale": "16", "use_angles": "0"}, 
"spawnPoints": [{"StartDisabled": "0", "TeamNum": "2", "angles": "0 0 0", "classname": "info_player_teamspawn", "controlpoint": "cp_red1", "id": "5459", "origin": "-5328 1120 24"} ...], 
"tournamentStage": null, 
"version": 3869
}
```

## Getting Started

* Clone this repository.
* Download and install Java, and locate the `java.exe` binary.
* Download and install Python 2 or 3.
* Download [BSPSource](https://developer.valvesoftware.com/wiki/BSPSource) and place the `.jar` in the same folder as you just checked out from this repository.
* Open up `map_data_gatherer.py` in your favorite text Editor and change the `JAVA_EXEC` and `MAPS_DIR` according to your system. The `MAPS_DIR` is the location where the `.bsp` files are located you want to extract metadata from.
* Open command line, navigate to this repository on your local disk and execute `python map_data_gatherer.py`.
* Wait for completion, there should appear a `json` file in your `./metadata` folder.