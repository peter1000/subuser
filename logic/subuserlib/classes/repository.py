#!/usr/bin/env python
# This file should be compatible with both Python 2 and 3.
# If it is not, please file a bug report.

"""
A repository is a collection of ``ImageSource`` s which are published in a git repo.
"""

#external imports
import os,shutil,io,json
#internal imports
import subuserlib.subprocessExtras
from subuserlib.classes.userOwnedObject import UserOwnedObject
from subuserlib.classes.imageSource import ImageSource
from subuserlib.classes.describable import Describable
from subuserlib.classes.gitRepository import GitRepository

class Repository(dict,UserOwnedObject,Describable):
  def __init__(self,user,name,gitOriginURI=None,gitCommitHash=None,temporary=False,sourceDir=None):
    """
    Repositories can either be managed by git, or simply be normal directories on the user's computer. If ``sourceDir`` is not set to None, then ``gitOriginURI`` is ignored and the repository is assumed to be a simple directory.
    """
    self.__name = name
    self.__gitOriginURI = gitOriginURI
    self.__lastGitCommitHash = gitCommitHash
    self.__temporary=temporary
    self.__sourceDir=sourceDir
    UserOwnedObject.__init__(self,user)
    self.__gitRepository = GitRepository(self.getRepoPath())
    self.loadProgramSources()

  def getName(self):
    return self.__name

  def getURI(self):
    if self.isLocal():
      return self.getSourceDir()
    else:
      return self.getGitOriginURI()

  def getSourceDir(self):
    return self.__sourceDir

  def getGitOriginURI(self):
    return self.__gitOriginURI

  def getGitRepository(self):
    return self.__gitRepository

  def getDisplayName(self):
    """
    How should we refer to this repository when communicating with the user?
    """
    if self.isTemporary():
      if self.isLocal():
        return self.__sourceDir
      else:
        return self.getGitOriginURI()
    else:
      return self.getName()

  def describe(self):
    print("Repository: "+self.getDisplayName())
    print("------------")
    if self.isLocal():
      print("Is a local(non-git) repository.")
      if not self.isTemporary():
        print("Located at: " + self.getRepoPath())
    if self.isTemporary():
      print("Is a temporary repository.")
    else:
      if not self.isLocal():
        print("Cloned from: "+self.getGitOriginURI())
        print("Currently at commit: "+self.getGitCommitHash())
    
  def getRepoPath(self):
    """ Get the path of the repo's sources on disk. """
    if self.isLocal():
      return self.__sourceDir
    else:
      return os.path.join(self.getUser().getConfig()["repositories-dir"],self.getName())

  def getRepoConfigPath(self):
    return os.path.join(self.getRepoPath(),".subuser.json")

  def getRepoConfig(self):
    """
    Either returns the config as a dictionary or None if no configuration exists or can be parsed.
    """
    if self.isLocal() and os.path.exists(self.getRepoConfigPath()):
      with io.open(self.getRepoConfigPath(),"r",encoding="utf-8") as configFile:
        configFileContents = configFile.read()
    elif not self.isLocal() and ".subuser.json" in self.getGitRepository().lsFiles(self.getGitCommitHash(),"./"):
      configFileContents = self.getGitRepository().show(self.getGitCommitHash(),"./.subuser.json")
    else:
      return None
    try:
      return json.loads(configFileContents)
    except ValueError as ve:
      # TODO we should probably exit and tell the user loudly that something isn't right.
      self.getRegistry().log("Error parsing .subuser.json file for repository "+self.getName()+":\n"+str(ve))
      return None

  def getSubuserRepositoryRoot(self):
    """
    Get the path of the repo's subuser root on disk on the host.
    """
    return os.path.join(self.getRepoPath(),self.getSubuserRepositoryRelativeRoot())

  def getSubuserRepositoryRelativeRoot(self):
    """
    Get the path of the repo's subuser root on disk on the host.
    """
    repoConfig = self.getRepoConfig()
    if repoConfig:
      if "subuser-repository-root" in repoConfig:
        if repoConfig["subuser-repository-root"].startswith("../"):
          raise ValueError("Paths in .subuser.json may not be relative to a higher directory.")
        return repoConfig["subuser-repository-root"]
    return "./"

  def isTemporary(self):
    return self.__temporary

  def isLocal(self):
    if self.__sourceDir:
      return True
    return False

  def removeGitRepo(self):
    """
    Remove the downloaded git repo associated with this repository from disk.
    """
    if not self.isLocal():
      shutil.rmtree(self.getRepoPath())

  def updateSources(self):
    """ Pull(or clone) the repo's ImageSources from git origin. """
    if self.isLocal():
      return
    if not os.path.exists(self.getRepoPath()):
      new = True
      subuserlib.subprocessExtras.call(["git","clone",self.getGitOriginURI(),self.getRepoPath()])
    else:
      new = False
      self.getGitRepository().checkout("master")
      self.getGitRepository().run(["pull"])
    if self.updateGitCommitHash():
      if not new:
        self.getUser().getRegistry().logChange("Updated repository "+self.getDisplayName())
      self.loadProgramSources()

  def loadProgramSources(self):
    """
    Load ProgramSources from disk into memory.
    """
    if self.isLocal():
      imageNames = filter(lambda f: os.path.isdir(os.path.join(self.getSubuserRepositoryRoot(),f)) and not f == ".git",os.listdir(self.getSubuserRepositoryRoot()))
    else:
      if not os.path.exists(self.getRepoPath()):
        self.updateSources()
      imageNames = self.getGitRepository().lsFolders(self.getGitCommitHash(),self.getSubuserRepositoryRelativeRoot())
      if self.getSubuserRepositoryRelativeRoot() != "./":
        imageNames = [os.path.basename(path) for path in imageNames]
    for imageName in imageNames:
      self[imageName] = ImageSource(self.getUser(),self,imageName)

  def updateGitCommitHash(self):
    """
    Update the internally stored git commit hash to the current git HEAD of the repository.
    Returns True if the repository has been updated.
    Otherwise false.
    """
    if self.isLocal():
      return None
    (returncode,output) = self.getGitRepository().runCollectOutput(["show-ref","-s","--head"])
    if returncode != 0:
      raise OSException("Running git in "+self.getGitRepository().getPath()+" with args "+str(["show-ref","-s","--head"])+" failed.")
    newCommitHash = output.split("\n")[0]
    updated = not newCommitHash == self.__lastGitCommitHash
    self.__lastGitCommitHash = newCommitHash
    return updated

  def getGitCommitHash(self):
    return self.__lastGitCommitHash
