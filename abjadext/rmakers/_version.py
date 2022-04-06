__version_info__ = (3, 7)
__version__ = ".".join(str(x) for x in __version_info__[:3]) + "".join(
    __version_info__[3:] or []
)
