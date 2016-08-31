#!/usr/bin/env python

#   Executes backup operations based on the instructions in the JSON input file
#
#   For example:
#       syncmate backupList.json
#
#       Will make backups of all the entries in backupList.json as specified
#       on its backup drives.
#       
#   See included documentation for more information on the JSON format
#

import argparse
import os
import json
import subprocess
import multiprocessing

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'    

def notify(options, message):
    """ Displays information about what is happening"""
    if options.verbose:
        print message

def notice(options, message):
    notify(options, bcolors.OKBLUE + message + bcolors.ENDC)

def warning(options, message):
    notify(options, bcolors.WARNING + message + bcolors.ENDC)

def fail(options, message):
    notify(options, bcolors.FAIL + message + bcolors.ENDC)

def terminate(message):
    """ Finishes the execution of the program with an exit message"""
    print bcolors.FAIL + message + bcolors.ENDC
    exit()


#
# Class: Backup Drive
# Holds an unique drive and the tokens that must perform backup operations over it
#
class BackupDrive:
    """A drive to perform a list of backup operations"""
    
    backupDrives = []       # A static list of all registered backup drives
    badDrives = []          # Also, remember our invalid drives
    
    # Path expander utility
    @staticmethod
    def expandPath(mountPoint, deviceName, isAbsolute):
        """Gets the path to the provided device"""

        expandedPath = os.path.expanduser(os.path.expandvars(deviceName))
        
        # create the actual path
        if isAbsolute:
            return expandedPath
        else:
            return mountPoint + expandedPath
        
    
    # A sort of drive dispenser. Use it to create new drives
    @classmethod
    def getDrive(cls, mountPoint, deviceName, options):
        """Creates and returns a new drive for backups. If the drive already exists, returns the object in file"""
        
        # See if we have a drive option for this device        
        absPath = BackupDrive.expandPath(mountPoint, deviceName, True)
        relPath = BackupDrive.expandPath(mountPoint, deviceName, False)
        existing = [drive for drive in cls.backupDrives if drive.path == absPath or drive.path == relPath]
        if len(existing):
            return existing[0]

        # We don't have it. Create one.
        drive = None
        if os.path.isdir(absPath):            
            drive = BackupDrive(absPath, options)
        elif os.path.isdir(relPath):
            drive = BackupDrive(relPath, options)
            
        if (drive != None) and (drive.isValid()):
            notice(options, "Found drive " + relPath)
            cls.backupDrives.append(drive)
            return drive
        else:
            if not relPath in cls.badDrives:
                warning(options,"Skipping " + relPath + " (disconnected or not available)")
                cls.badDrives.append(relPath)
            return None
            
    # Initialization
    def __init__(self, deviceName, options):
        """Initializes a new drive. Make sure you call getDrive instead"""
        
        # Absolute path to the drive
        self.path = "" 

        # Backup items 
        self.items = []

        # Physical device name 
        path = deviceName
        
        # Test: If the path is correct, we're in business. In theory, you called
        # getDrive and this test has been made, but nothing prevents someone from
        # attempting to create a drive manually.
        if os.path.isdir(path) == True:
            self.path = path
            
    # Determines if this drive is valid
    def isValid(self):
        return self.path != ""
    
    # Registers a new item for backup
    def addBackupItem(self, item):
        # We could test to make sure we don't have an item like this already, but we'd have
        # to go through all included backup list options, all specified exclusions, and any future
        # property. Instead, rely on the fact that rsync knows that it is doing. 
        self.items.append(item)

    # Triggers the backup action of all of the components in this drive
    def performBackup(self, options):
        for item in self.items:
            item.performBackup(options,self.path)
            

#
# Class: Backup object
# Keeps information about a single backup object
#
class BackupItem:
    """Stores basic information about a backup item"""
        
    # Initializer: Creates a backup item from the expected format <folder>:<destination>
    def __init__(self, tokens):

        self.name = ""      # Name of this backup item
        self.valid = False  # Tells if the current object has a valid source and dest
        self.exclude = []   # Files or patterns to exclude
        self.backups = []   # A list of (source,dest) tuples to perform backups on        
        
        self.__parseTokens(tokens)
                
    # private: Parse the provided tokens
    def __parseTokens(self, tokens):
        
        if "name" in tokens:
            self.name = tokens['name']

        if "exclude" in tokens:
            self.exclude = tokens["exclude"]

        if "backup" in tokens:
            for backupEntry in tokens["backup"]:
                for entryObject in backupEntry:
                    backupPath = os.path.expanduser(os.path.expandvars(entryObject))
                if os.path.isdir(backupPath):
                    self.backups.append((backupPath, backupEntry[entryObject]))
                else:
                    notify(options, "Invalid backup path: " + backupPath + ", skipping")

        else:
            notify(options, "No backup items found in entry %s, skipping." %  self.name)

        # We are valid if we have at least one backup and at least one backup item
        if len(self.backups):
            self.valid = True
            
    # Tells if this object contains valid information
    def isValid( self ):
        return self.valid

    # Do one backup item
    def __backupOneItem(self, options, drive, source, dest):

        # Actual destination
        destination = "%s/%s" % (drive, dest)

        notify(options,"---------------------------------------------------------------------")
        notify(options,"backing up " + source + " into: " + destination)

        if os.path.isdir(destination) == False:
            notice(options, "Creating directory "+ destination + "...")
            try:
                os.makedirs(destination)
            except OSError:
                fail("Failed to create directory " + destination +", skipping...")
                return                    
        else:
            notify(options,"Destination ok: " + destination )
        notify(options,"---------------------------------------------------------------------")

        # Base command. Quick and dirty:            
        if options.verbose:
            command = ['rsync', '-avzru', '--progress']
        else:
            command = ['rsync', '-azru']
            
        # Use this for a dry run
        if options.dry:
            command.append('--dry-run')
        #command = ['rsync', '--dry-run', '-avzru']                
                        
        # Exclusions
        for exclusion in self.exclude:
            command.append("--exclude=%s" % exclusion)
                                            
        # Source and destination
        command.append(source)
        command.append(destination)
        
        # Execute
        subprocess.call(command)
        #print command

    
    # performs the backup operation as described in our information
    def performBackup(self, options, path ):
        if self.valid == True:
            for backup in self.backups:
                self.__backupOneItem(options, path, backup[0], backup[1])
    
#
# Processes lines from the input file.
# 
def processInputFile(jsonData, options):
    """Based on the data found in the input file, parse each backup token and return an array of backup objects"""

    if 'name' in jsonData:
        notify(options, "Running %s" % jsonData['name'])
    else:
        notify(options, "Running backup actions")

    if not 'actions' in jsonData or not isinstance(jsonData['actions'], list):
        terminate('No valid actions entry found in %s, terminating' % options.script )

    # Find a mount point
    mountPoint = jsonData['mount'] if 'mount' in jsonData else "/Volumes/"
    mountPoint = os.path.expanduser(os.path.expandvars(mountPoint))
    notify(options, "Using mounting point %s" % mountPoint )

    for action in jsonData['actions']:

        # Extract drives
        drives = []
        if not 'drives' in action:
            notify(options, "No drives found on backup action. Skipping")
            continue

        for driveName in action['drives']:
            drive = BackupDrive.getDrive(mountPoint, driveName, options)
            if drive != None:
                drives.append(drive)

        if not len(drives):
            notify(options, "No valid drives found on backup action. Skipping")
            continue

        # Extract items
        if not 'items' in action or not isinstance(action['items'], list):
            notify(options, "No valid items list found on backup action. Skipping")
            continue

        # Create item objects. Add them to our available drives (quick 'n dirty)
        for item in action['items']:
            backupItem = BackupItem(item)
            if backupItem.isValid():
                for drive in drives:
                    drive.addBackupItem(backupItem)

    return
                    
def perform_backup( drive, options ):
    drive.performBackup(options)

        
if __name__ == '__main__':
            
    # parse arguments. Input file required.
    parser = argparse.ArgumentParser(description="Utility for the automation of backup tasks")
    parser.add_argument("script", help="A JSON file with the configuration of all backup operations")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display lots of data about what is happening")
    parser.add_argument("-m", "--multithreaded", action="store_true", help="If specified, perform all backup operations concurrently per drive")
    parser.add_argument("-n", "--dry", action="store_true", help="Show what the results would be, but do not execute backup operations")
    options = parser.parse_args()

    # We have an input file. See if we can parse backup tokens out of it
    # (Read about the EAFP style on python.org)
    try:
        raw = open(options.script)
    except IOError:
        terminate("Error reading " + options.script + ", make sure the file exists, and is accessible")
    else:        
        try:
            notify(options, "Opening %s" % options.script)
            data = json.load(raw)
        except:
                terminate("Error processing " + options.script + ", is this a valid json file?")

    # We have data. Parse it
    processInputFile(data, options)

    # After parsing command options and output drives, we must have at least one of them
    if len(BackupDrive.backupDrives) == 0:
        terminate("Error: No valid backup volumes found. Make sure output options are correct.")
    
    # Multithreaded or single-threaded?
    if (options.multithreaded):
        notify(options, 'Performing multithreaded backup')
        for drive in BackupDrive.backupDrives:
            multiprocessing.Process(target=drive.performBackup,args=(options,)).start()
    else:
        notify(options, 'Performing sequential backup')
        for drive in BackupDrive.backupDrives:
            drive.performBackup(options)

    notify(options, "done")
    exit()
    
