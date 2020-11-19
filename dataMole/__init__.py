import os

# Save the path to the root dir. This is useful when building docs
rootdir = os.getcwd()
cwdName = os.path.basename(os.path.normpath(rootdir))
if cwdName == 'docs':
    rootdir = os.path.join(rootdir, '..')
