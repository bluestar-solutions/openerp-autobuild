# Autobuild for OpenERP

Autobuild for OpenERP is an utility script designed to simply configure, debug, deploy and run customized OpenERP applications.

## Installation

`sudo apt-get install openerp-autobuild`

## Usage

### Configuration file

#### oebuild.conf - structure

	DEPENDENCIES = "dependencies"
	SCM = "scm"
	SCM_GIT = "git"
	SCM_BZR = "bzr"
	URL = "url"
	BZR_REV = "bzr-rev"
	GIT_BRANCH = "git-branch"
	DESTINATION = "destination"
	OEBUILD_VERSION = "oebuild-version"
	ADDONS_PATH = "addons-path"
	PROJECT = "project"

	OPENERP_TYPE = {
	"type": "object",
	"properties": {
	    URL: {"type": "string", "format": "uri"},
	    BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": False},
	}
	}
	DEPENDENCY_GIT = {
	    "type": "object",
	    "properties": {
		SCM: {"type": "string", "pattern": SCM_GIT},
		URL: {"type": "string", "format": "uri"},
		GIT_BRANCH: {"type": "string", "required": True},
		DESTINATION: {"type": "string", "format": "uri"},
		ADDONS_PATH: {"type": "string", "format": "uri", "required": False},
	    },
	}
	DEPENDENCY_BZR = {
	    "type": "object",
	    "properties": {
		SCM: {"type": "string", "pattern": SCM_BZR},
		URL: {"type": "string", "format": "uri"},
		BZR_REV: {"type": "string", "pattern": "^[0-9]+$", "required": True},
		DESTINATION: {"type": "string", "format": "uri"},
		ADDONS_PATH: {"type": "string", "format": "uri", "required": False},
	    },
	}
	OEBUILD_SCHEMA = {
	    "type": "object",
	    "properties": {
		OEBUILD_VERSION: {"type": "string", "pattern": "^[0-9]+|.[0-9]+$", "required": True},
		PROJECT: {"type": "string", "pattern": "^[a-z|0-9|-]+$"},
		"openerp-server": OPENERP_TYPE,
		"openerp-addons": OPENERP_TYPE,
		"openerp-web": OPENERP_TYPE,
		DEPENDENCIES: {
		    "type": "array",
		    "items": {"type": [DEPENDENCY_GIT, DEPENDENCY_BZR]}
		}
	    }
	}
	
#### oebuild.conf - example

	{
		"oebuild-version": "1.6",
		"project": "my_project_name",
		"openerp-server": {
			"url": "bzr://my-server.org:8080/openerp-7.0-server",
			"bzr-rev": "5463"
		},
		"openerp-addons": {
			"url": "bzr://my-server.org:8080/openerp-7.0-addons",
			"bzr-rev": "8963"
		},
		"openerp-web": {
			"url": "bzr://my-server.org:8080/openerp-7.0-web",
			"bzr-rev": "4007"
		},
		"dependencies": [{
			"scm": "git",
			"url": "ssh://username@my-other-server.edu:4242/my-dependencies.git",
			"git-branch": "my-branch",
			"destination": "destination_path",
			"addons-path": "/"
		}]
	}

### Goals

* **run** : Run OpenERP server with default parameters. Logs only INFO level messages.
* **debug** : Same as run but also logs DEBUG level messages.
* **test** : Run OpenERP server in test mode. In this mode, the server will use another database (named after your project's name) to load demo data and perform designated tests.
* **assembly** : Build a package with your custom addons and their dependencies in order to deploy the application.
* **init-eclipse** : Initialize an existing project as a _Eclipse Pydev Project_

### Shared parameters

* **-m**, **--modules** : Specify which custom module to load. If omitted, all custom modules will be loaded.
* **-p**, **--tcp-port** : TCP port of the server (default:8069).
* **--update** : Update server and dependencies with lastest version.

### Run parameters

None

### Debug parameters

None

### Test parameters

* **--test-commit** : Commit changes made during tests to database. If omitted, database will remain the same as before the tests.
* **--db-name** : Specify custom database name for the tests. ***WARNING*** if database alread exists, it's data may be altered.
* **--force-install** : Force a new install of the modules. The database will be dropped if existing and built-in tests will be run.
* **--analyze** : Analyze logs and stop OpenERP. Use it with continuous integration.

### Assembly parameters

* **--with-oe** : Build the package with current version of OpenERP in order to deploy a fully runnable application.

### Init-eclipse parameters

None

### Some examples

Run server and load _mymodule_ and _othermodule_  
`oebuild run --modules mymodule,othermodule`

Run server in test mode on a new database named _my-custom-tests_ for continuous integration  
`oebuild test --db-name my-custom-tests --force-install --analyze`

Build a fully runnable package  
`oebuild assembly --with-oe`

## Credits

Bluestar Solutions Sàrl  
Rue de la Maladière 23  
CH-2000 Neuchâtel

## License

TODO: Write license
