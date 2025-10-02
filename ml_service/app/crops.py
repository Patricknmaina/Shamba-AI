"""Canonical crop definitions and normalization helpers."""

from enum import Enum
from typing import Dict, List


class Crop(str, Enum):
    """Supported crops exposed via the insights API."""

    MAIZE = "maize"
    BEANS = "beans"
    TOMATO = "tomato"
    POTATO = "potato"
    RICE = "rice"
    WHEAT = "wheat"
    SORGHUM = "sorghum"
    CASSAVA = "cassava"
    SWEET_POTATO = "sweet potato"
    BANANA = "banana"
    GROUNDNUT = "groundnut"
    SOYBEAN = "soybean"
    COWPEA = "cowpea"
    PIGEON_PEA = "pigeon pea"
    MILLET = "millet"
    SUNFLOWER = "sunflower"
    ONION = "onion"
    CABBAGE = "cabbage"
    CARROT = "carrot"
    CHILI = "chili"


SUPPORTED_CROPS: List[str] = [crop.value for crop in Crop]
SUPPORTED_CROP_SET = set(SUPPORTED_CROPS)

CROP_ALIASES: Dict[str, str] = {
    "maize": Crop.MAIZE.value,
    "beans": Crop.BEANS.value,
    "tomatoes": Crop.TOMATO.value,
    "potatoes": Crop.POTATO.value,
    "rices": Crop.RICE.value,
    "wheats": Crop.WHEAT.value,
    "sorghums": Crop.SORGHUM.value,
    "cassavas": Crop.CASSAVA.value,
    "sweetpotato": Crop.SWEET_POTATO.value,
    "sweet potatoes": Crop.SWEET_POTATO.value,
    "bananas": Crop.BANANA.value,
    "groundnuts": Crop.GROUNDNUT.value,
    "soybeans": Crop.SOYBEAN.value,
    "cowpeas": Crop.COWPEA.value,
    "pigeonpea": Crop.PIGEON_PEA.value,
    "pigeon peas": Crop.PIGEON_PEA.value,
    "millets": Crop.MILLET.value,
    "sunflowers": Crop.SUNFLOWER.value,
    "onions": Crop.ONION.value,
    "cabbages": Crop.CABBAGE.value,
    "carrots": Crop.CARROT.value,
    "chilli": Crop.CHILI.value,
    "chillies": Crop.CHILI.value,
    "chilies": Crop.CHILI.value,
}


def normalize_crop(crop_name: str) -> str:
    """Map user-provided crop name to canonical form when possible."""
    if not crop_name:
        return ""

    key = crop_name.lower().strip()
    if key in SUPPORTED_CROP_SET:
        return key

    return CROP_ALIASES.get(key, key)


def get_supported_crops() -> List[str]:
    """Return canonical crop names."""
    return SUPPORTED_CROPS.copy()
