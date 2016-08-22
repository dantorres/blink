# Syncmate

A very simple script for keeping and maintaining backups of your stuff. This is
basically a higher-level layer on top of your system's rsync command.

## Usage

Simply tell the script to process a file with all of your backup operations, like so:

	syncmate.py backups.json

Optionally, run The following command to get a descripton of all available options:

	syncmate.py --help

## JSON File Syntax

A JSON backup file contains the following elements:

- The name of our backup run
- An array of backup operations.
- Optionally, a mounting point for your backup drives

Each operation contains the following:

- The names of the drives you want to copy things into
- A number of backup operations in source: destiny format.
- Optional parameters, like the files to exclude.

## Example

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
