import wx
import os


ICON_PATH = os.path.join("images", "icon.ico")


def get_image(filename: str) -> wx.Image:
    """loads an image from file and converts to bitmap

    Args:
        filename (str): name of the file to load from the image directory

    Raises: FileNotFoundError if no file found

    Returns:
        wx.Image: the converted bitmap
    """
    full_path = os.path.join("images", filename)
    if not os.path.exists(full_path):
        raise FileNotFoundError(
            f"{full_path} does not exist. Please check the image location"
        )
    image = wx.Image(full_path, wx.BITMAP_TYPE_ANY)
    return image
