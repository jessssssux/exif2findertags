""" Read and write Spotlight metadata stored in com.apple.metadata extended attributes

osxmetadata reads attributes with MDItemCopyAttribute, which returns values from the
Spotlight index rather than from the file. On a file that is not indexed (a new file,
a temporary directory, an external volume with indexing off) every read returns None.
MDItemSetAttribute also silently ignores some attributes (for example kMDItemDescription,
kMDItemKeywords, kMDItemTitle and kMDItemHeadline on recent macOS). Spotlight imports
com.apple.metadata:<attribute> extended attributes, so reading and writing those directly
works whether or not the file is indexed.
"""

import plistlib
import typing as t

import osxmetadata
import xattr

__all__ = [
    "XATTR_PREFIX",
    "read_metadata",
    "write_metadata",
    "remove_metadata",
    "read_finder_comment",
    "write_finder_comment",
]

XATTR_PREFIX = "com.apple.metadata:"
kMDItemFinderComment = "kMDItemFinderComment"


def read_metadata(filename: str, attribute: str) -> t.Any:
    """Return the value of kMDItem attribute stored on filename or None if not set"""
    try:
        data = xattr.getxattr(filename, f"{XATTR_PREFIX}{attribute}")
    except OSError:
        return None
    try:
        return plistlib.loads(data)
    except Exception:
        return None


def write_metadata(filename: str, attribute: str, value: t.Any):
    """Write value to kMDItem attribute on filename as a binary plist"""
    xattr.setxattr(
        filename,
        f"{XATTR_PREFIX}{attribute}",
        plistlib.dumps(value, fmt=plistlib.FMT_BINARY),
    )


def remove_metadata(filename: str, attribute: str):
    """Remove kMDItem attribute from filename if present"""
    try:
        xattr.removexattr(filename, f"{XATTR_PREFIX}{attribute}")
    except OSError:
        pass


def read_finder_comment(filename: str) -> t.Optional[str]:
    """Return the Finder comment for filename or None if not set"""
    return read_metadata(filename, kMDItemFinderComment) or None


def write_finder_comment(filename: str, comment: t.Optional[str]):
    """Set or clear the Finder comment for filename

    Finder keeps its own copy of the comment in .DS_Store, so the comment is set through
    Finder (via osxmetadata) to make it show in Get Info, then written to the extended
    attribute so it is on the file even if Finder could not be reached.
    """
    if comment:
        osxmetadata.OSXMetaData(filename).findercomment = comment
        write_metadata(filename, kMDItemFinderComment, comment)
    elif read_metadata(filename, kMDItemFinderComment) is not None:
        # osxmetadata raises if asked to remove a comment that is not there
        osxmetadata.OSXMetaData(filename).findercomment = None
        remove_metadata(filename, kMDItemFinderComment)
