from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ibeat-mt")
except PackageNotFoundError:
    # package is not installed
    __version__ = "unknown"


from . import (
    stage_01_download,
    stage_02_clean_database,
    stage_03_combine,
    stage_04_mdr,
    stage_05_map,
    stage_06_align,
    stage_07_display,
    stage_08_measure
)
