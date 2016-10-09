# Blink

A very simple script for keeping and maintaining backups of your stuff. This is
basically a higher-level layer on top of your system's rsync command.

I wrote it as a simple solution to keep my photography work backed up in a bunch of mobile
drives whilst on the road, as well as my multiple home backup destinations. 

## Usage

Simply tell the script to process a JSON file with all of your backup operations, like so:

	blink.py backups.json

Optionally, run The following command to get a descripton of all available options:

	blink.py --help

## JSON File Syntax

A JSON backup file contains the following elements:

- The name of our backup run
- An array of backup operations.
- Optionally, a mounting point for your backup drives

Each operation contains the following:

- The names of the drives you want to copy things into
- A number of backup operations in source: destination format.
- Optional parameters, like the files to exclude.

## Example

Here is a basic example that performs two backup actions:

- The first action operates over the _MyExternalDrive1_ and _MyKeychainDrive_ drives, if 
they are connected. It will perform two backups: *Documents*, and *Projects*. The first
operation copies the contents of your docs/ folder into a folder in your backup
drives called Backups/docs, and the second operation copies three project folders into 
their respective locations on Backups/Projects, excluding files with the .tmp and the .old extensions.

- The second action will trigger if the drive called *MyPrivateDrive* is connected. It
will copy the contents of your ~/files/private folder into Backups/private (on the mentioned
drive)

```json
{
	"name": "My backup example",
	"actions":[
		{
			"drives": ["MyExternalDrive1", "MyKeychainDrive"],
			"items": [
				{
					"name": "Documents",
					"backup": [
						{ "~/docs": "Backups"}
					]
				},

				{
					"name": "Projects",
					"exclude": [
						"*.tmp",
						"*.old"
					],
					"backup": [
						{ "~/Projects/mine": "Backups/Projects" },
						{ "~/Projects/business": "Backups/Projects" },
						{ "~/Projects/private": "Backups/Projects" }
					]
				}
			]
		}, 

		{
			"drives": ["MyPrivateDrive"],
			"items": [
				{
					"name": "Private important files",
					"backup": [
						{ "~/Files/Private": "Backups" }
					]
				}
			]
		}
	]
}
```
