""" Main script for generating Map files. """
import os
import pprint
import sys


if __name__ == "__main__" and __package__ is None:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xero_map_gen.core import main

if __name__ == "__main__":
    main()
