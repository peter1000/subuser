#!/usr/bin/env python
# This file should be compatible with both Python 2 and 3.
# If it is not, please file a bug report.

"""
The ``User`` object is the base object which owns all other objects in a running subuser instance.
"""

#external imports
import getpass
import os
import sys
#internal imports
from subuserlib.classes import registry
from subuserlib.classes import config
from subuserlib.classes import installedImages
from subuserlib.classes.docker import dockerDaemon
from subuserlib import test
from subuserlib import paths


class User(object):
  """
  This class provides a "base" User object used by subuser.  This is the stem of a tree like data structure which holds all of the various objects owned by a given user.

  You create a new User object by passing the username and home dir of the user.

  >>> import subuserlib.classes.user
  >>> u = subuserlib.classes.user.User("root","/root/")
  >>> u.homeDir
  '/root/'
  """

  def __init__(self,name=None,homeDir=None):
    self.__config = None
    self.__registry = None
    self.__installedImages = None
    self.__dockerDaemon = None
    self.__runtimeCache = None
    if os.path.exists(os.path.join(paths.getSubuserDir(),"installed-images.json")):
      sys.exit("""Hey, it looks like you are using an old version of subuser.  First of, thanks for being an early adopter!  That really means a lot to me :)  Subuser has recently undergone a major re-write.  Unfortunately, you'll have to set up everything all over again.  You can find your subuser home dirs in subuser/homes.  The new version of subuser keeps them in ~/.subuser/homes.  You can find out all about the different locations subuser serializes to by looking in the enw config.json file.  I hope I'll have some docs up soon at subuser.org.  Sorry for the inconvenience.

To disable this message delete your subuser/installed-programs.json file.
""")
    if name:
      self.name = name
    else:
      try:
        self.name = getpass.getuser()
      except KeyError:
        # We use a broken setup when generating documentation...
        self.name = "I have no name!"

    if homeDir:
      self.homeDir = homeDir
    else:
      if test.testing:
        self.homeDir = "/home/travis/test-home"
      else:
        self.homeDir = os.path.expanduser("~")
 
  def getConfig(self):
    """
    Get the user's :doc:`Config <config>` object.

    Note: the user's config will be loaded the first time this is called.
    """
    if self.__config == None:
      self.__config = config.Config(self)
    return self.__config

  def getRegistry(self):
    """
    Get the user's subuser :doc:`Registry <registry>`.

    Note: the registry will be loaded the first time this is called.
    """
    if self.__registry == None:
      self.__registry = registry.Registry(self)
    return self.__registry

  def reloadRegistry(self):
    """
    Reload registry from disk.
    """
    self.__registry = None

  def getInstalledImages(self):
    """
    Get the user's  :doc:`InstalledImages <installed-images>` list.

    Note: the installed images list will be loaded the first time this is called.
    """
    if self.__installedImages == None:
      self.__installedImages = installedImages.InstalledImages(self)
    return self.__installedImages

  def getDockerDaemon(self):
    """
    Get the :doc:`DockerDaemon <docker>` object.  You will use this to communicate with the Docker daemon.
    """
    if self.__dockerDaemon == None:
      self.__dockerDaemon = dockerDaemon.DockerDaemon(self)
    return self.__dockerDaemon
