import glob
from itertools import chain
import os


def dataset_label(path):
    """
    :param path: Path to the image dataset
    :return: b_names: Directory name of each item
             labels: A unique ID is given each directory name
             fnames: List of path to image files
    """
    # Path to the image dataset
    IMG_DIR = path

    # Directory name of each item
    b_names = glob.glob("{}/*".format(IMG_DIR))

    # List of path to image files
    fnames = [glob.glob("{}/*.jpg".format(b)) for b in b_names]
    fnames = list(chain.from_iterable(fnames))

    # A unique ID is given each directory name
    labels = [os.path.basename(os.path.dirname(fn)) for fn in fnames]
    b_names = [os.path.basename(b) for b in b_names]
    labels = [b_names.index(l) for l in labels]
    return b_names, labels, fnames
