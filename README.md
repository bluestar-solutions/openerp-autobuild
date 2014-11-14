# Autobuild for OpenERP

Autobuild for OpenERP is an utility script designed to simply configure, debug, deploy and run customized OpenERP applications.

## Installation

### From Ubuntu PPA

	sudo add-apt-repository ppa:bluestar-dev-team/openerp-autobuild
	sudo apt-get update
	sudo apt-get install openerp-autobuild

### From archive

Download archive, extract it and run install.sh script

#### Requirements

* **Source headers**: Python 2.7 (python), OpenLDAP (libldap2), libsasl2, libxml2, libxslt
* **Softwares**: pip, Bazaar (bzr), PostgreSQL version information tool (pg_config), virtualenv
* **Python libraries**: jsonschema, psycopg2, GitPython, argcomplete

The Python libraries can be installed with pip.

## Configuration

### User Settings

You can find your user setting under "~/.config/openerp-autobuild/oebuild_config.json", this file is
used to override default settings defined in "/etc/oebuild_config.json".

#### Options

* ``oebuild-version``: Specify the version of openerp-autobuild targeted by the configuration file.
* ``workspace``: Specify the directory used to store builded virtual environment (with OpenERP and dependencies) for each project.
* ``custom-configuration-files``: A list of alternative project configuration names. For instance, if you specify ``["mycompany", "me"]``, 
  oebuild.conf will be read and overrided firstly by oebuild-mycompany.conf (if file exists), and then by oebuild-me.conf (if file exists).
* ``openerp``: List of configured OpenERP series 
    * ``serie``: The serie name. If the name is defined in default configuration file, the following options will override the default.
    * ``server``: Bazaar url for the OpenERP server branch.
    * ``addons``: Bazaar url for the OpenERP addons branch.
    * ``web``: Bazaar url for the OpenERP web branch.
    * ``python-dependencies``: List of Python dependencies for this serie (will be downloaded and installed in virtualenv by pip).
        * ``name``: The pip name of the Python library.
        * ``specifier``: The pip version constraint specifier.
* ``default-serie``: The default serie used to configure new project by init goal.
* ``database``: The database connection settings.
    * ``host``: The database host (default localhost).
    * ``port``: The database port (default 5432).
    * ``user``: The database user (default openerp).
    * ``password``: The database password (default openerp).

### Project Settings

The default project settings are in oebuild.conf, located at the root of the concerned project. This file can be overridden by every oebuild-*.conf, 
if * is defined in your user settings custom-configuration-files list.

To create a new project with a default oebuild.conf, run (in a new project folder) :

	oebuild init

#### Options

* ``oebuild-version``: Specify the version of openerp-autobuild targeted by the configuration file.
* ``project``: The project name.
* ``openerp``: OpenERP serie to use for this project.
    * ``serie``: The serie name. This name have to be defined in default configuration fil or in user configuration file.
        * ``server``: Bazaar settings for the OpenERP server branch.
            * ``url``: Bazaar url to use.
            * ``bzr-rev``: Bazaar branch revision to use.        
        * ``addons``: Bazaar settings for the OpenERP addons branch.
            * ``url``: Bazaar url to use.
            * ``bzr-rev``: Bazaar branch revision to use.    
        * ``web``: Bazaar settings for the OpenERP web branch.
            * ``url``: Bazaar url to use.
            * ``bzr-rev``: Bazaar branch revision to use.          
* ``python-dependencies``: List of Python dependencies for this project (will be downloaded and installed in virtualenv by pip).
    * ``name``: The pip name of the Python library.
    * ``specifier``: The pip version constraint specifier.
* ``dependencies``: List of other OpenERP addons project dependency.
    * ``name``: The addons project name.
    * ``source``: The addons project source location.
        * ``scm``: The protocol used to get the project (git, bzr, local).
        * ``url``: The scm url or local path.
        * ``bzr-rev``: The Bazaar revision to used (only if scm=bzr).
        * ``git-branch``: The git branch to used (only if scm=git).

Only ``oebuild-version``, ``openerp`` and ``dependencies`` options can be overrided in a alternative configuration file.

### OpenERP Settings

With OpenERP Autobuild, OpenERP will use the file ".openerp-dev-default" located at the root of the project to get OpenERP run settings.

To create a new project with a default .openerp-dev-default, run (in a project folder) :

	oebuild init

### Goals

* **run** : Run OpenERP server with default parameters. Logs only INFO level messages.
* **debug** : Same as run but also logs DEBUG level messages.
* **test** : Run OpenERP server in test mode. In this mode, the server will use another database (named after your project's name) to load demo data and perform designated tests.
* **assembly** : Build a package with your custom addons and their dependencies in order to deploy the application.
* **init** : Initialize an empty OpenERP project with default configuration files
* **init-eclipse** : Initialize an existing project as a _Eclipse Pydev Project_

### Shared parameters

* **-m**, **--modules** : Specify which custom module to load. If omitted, all custom modules will be loaded.
* **-p**, **--tcp-port** : XML_RPC port of the server (default:8069).
* **-n**, **--netrpc-port** : NET_RPC port of the server (default:8070).
* **--no-update**: Bypass updates and try to launch with last parameters. 
* **--home-config**: Bypass default config with a specific configuration. 
* **--etc-config**: Bypass default config with a specific configuration. 

### Run parameters

None

### Debug parameters

None

### Test parameters

* **--test-commit** : Commit changes made during tests to database. If omitted, database will remain the same as before the tests.
* **--db-name** : Specify custom database name for the tests. ***WARNING*** if database alread exists, it's data may be altered.
* **--force-install** : Force a new install of the modules. The database will be dropped if existing and built-in tests will be run.
* **--analyze** : Analyze logs and stop OpenERP. Use it with continuous integration.
* **--stop-after-init** : Force OpenERP server to stop when tests are done.

### Assembly parameters

* **--with-oe** : Build the package with current version of OpenERP in order to deploy a fully runnable application.

### Init parameters

None

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

[GNU AFFERO GENERAL PUBLIC LICENSE, version 3](http://www.gnu.org/licenses/agpl-3.0.html)
