import requests
from zipfile import ZipFile
from io import BytesIO
import os

# change working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

VERSION_ID = "1.20.1"

# minecraft property encyclopedia urls
BLOCK_DATA_URL = "https://raw.githubusercontent.com/JoakimThorsen/MCPropertyEncyclopedia/main/data/block_data.json"
ITEM_DATA_URL = "https://raw.githubusercontent.com/JoakimThorsen/MCPropertyEncyclopedia/main/data/item_data.json"

# find client jar url
versions = requests.get(
    "https://launchermeta.mojang.com/mc/game/version_manifest.json"
).json()["versions"]

for version in versions:
    if version["id"] == VERSION_ID:
        version_url = version["url"]
        break

if not version_url:
    raise Exception("Version not found")

client_jar_url = requests.get(version_url).json()["downloads"]["client"]["url"]

# generate id list
blocks = requests.get(BLOCK_DATA_URL).json()
items = requests.get(ITEM_DATA_URL).json()
ids = []

for key in blocks["key_list"]:
    variants = blocks["properties"]["variants"]["entries"][key]

    if isinstance(variants, str):
        variants = [variants]

    for variant in variants:
        # is the variant available in survival?
        survival_available = blocks["properties"]["survival_available"]["entries"].get(
            key
        )

        if isinstance(survival_available, dict):
            survival_available = survival_available.get(variant) == "Yes"
        else:
            survival_available = survival_available is None

        # is the variant always placeable?
        always_placeable = blocks["properties"]["placement_condition"]["entries"].get(
            key
        )

        if isinstance(always_placeable, dict):
            always_placeable = always_placeable.get(variant) == "No"
        else:
            always_placeable = always_placeable is None

        # does the variant have an item?
        has_item = blocks["properties"]["exists_as_item"]["entries"].get(key)

        if isinstance(has_item, dict):
            has_item = has_item.get(variant) == "Yes"
        else:
            has_item = has_item is None

        # is the variant a full cube?
        full_cube = blocks["properties"]["full_cube"]["entries"].get(key)

        if isinstance(full_cube, dict):
            full_cube = full_cube.get(variant) == "Yes"
        else:
            full_cube = full_cube is None

        if survival_available and always_placeable and has_item and full_cube:
            try:
                ids.append(items["properties"]["id"]["entries"][variant])
            except:
                pass

# make sure blocks directory exists
if not os.path.exists("blocks"):
    os.makedirs("blocks")
else:
    for file in os.listdir("blocks"):
        os.remove(os.path.join("blocks", file))

# download latest assets
jar = requests.get(client_jar_url)

with ZipFile(BytesIO(jar.content)) as zip:
    for info in zip.infolist():
        if info.filename.startswith("assets/minecraft/textures/block"):
            if (
                ".mcmeta" in info.filename
                or f"{info.filename}.mcmeta" in zip.namelist()
            ):
                continue

            id = info.filename.split("/")[-1].split(".png")[0]

            # skip if not a valid block
            if id not in ids:
                continue

            with zip.open(info) as zip_file, open(f"blocks/{id}.png", "wb") as file:
                file.write(zip_file.read())
