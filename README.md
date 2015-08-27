# Autobuild for OpenERP

Autobuild for OpenERP is an utility script designed to simply configure, debug, deploy and run customized OpenERP applications.

## Installation

### From Ubuntu PPA

#### Stable

	sudo add-apt-repository ppa:bluestar-dev-team/openerp-autobuild
	sudo apt-get update
	sudo apt-get install openerp-autobuild
	
#### Release Candidate

	sudo add-apt-repository ppa:bluestar-dev-team/openerp-autobuild-rc
	sudo apt-get update
	sudo apt-get install openerp-autobuild
	
### Download From GitHub

https://github.com/bluestar-solutions/openerp-autobuild

* Download the archive and extract it or clone the git repository
* Run install.sh script

#### Requirements

* **Source headers**: Python 2.7 (python), OpenLDAP (libldap2), libsasl2, libxml2, libxslt
* **Softwares**: pip, Git (Git), Bazaar (bzr), PostgreSQL version information tool (pg_config), virtualenv
* **Python libraries**: jsonschema, psycopg2, GitPython, argcomplete

The Python libraries can be installed with pip.

## Configuration

### User Settings

You can find your user setting under "~/.config/openerp-autobuild/oebuild_config.json", this file is
used to override default settings defined in "/etc/oebuild_config.json".

#### Options

* ``oebuild-version``: Specify the version of openerp-autobuild targeted by the configuration file.
* ``workspace``: If set, override the default directory used to store builded virtual environment (with OpenERP and dependencies) for each project.
* ``custom-configuration-files``: A list of alternative project configuration names. For instance, if you specify ``["mycompany", "me"]``, 
  oebuild.conf will be read and overrided firstly by oebuild-mycompany.conf (if file exists), and then by oebuild-me.conf (if file exists).
* ``module_author``: Specify the author to set for module.create goal.
* ``website``: Specify the author website to set for module.create goal.
* ``openerp``: List of configured OpenERP series. You can override settings of a default serie or add a custom one.
    * ``serie``: The serie name. If the name is defined in default configuration file, the following options will override the default.
    * ``source``: Git settings for the OpenERP repository.
    	* ``url``: Git URL for the OpenERP repository.
    	* ``git-branch``: Branch name for the OpenERP repository.
    	* ``git-commit``: Commit SHA-1 to use (override git-branch if defined).
    * ``python-dependencies``: List of Python dependencies for this serie (will be downloaded and installed in virtualenv by pip).
        * ``name``: The pip name of the Python library.
        * ``specifier``: The pip version constraint specifier.
        * ``options``: Add options for pip call.
* ``default-serie``: If set, override the default serie used to configure new project by init goal.
* ``database``: The database connection settings.
    * ``host``: The database host (default localhost).
    * ``port``: The database port (default 5432).
    * ``user``: The database user (default openerp).
    * ``password``: The database password (default openerp).

### Project Settings

The default project settings are in oebuild.conf, located at the root of the concerned project. This file can be overridden by every oebuild-*.conf, 
if * is defined in your user settings custom-configuration-files list.

To create a new project with a default oebuild.conf, run (in a new project folder) :

	oebuild project.init

#### Options

* ``oebuild-version``: Specify the version of openerp-autobuild targeted by the configuration file.
* ``project``: The project name.
* ``openerp``: OpenERP serie to use for this project.
    * ``serie``: The serie name. This name have to be defined in default configuration file or in user configuration file.
        * ``source``: Git settings for the OpenERP repository. Used to override serie default settings.
            * ``url``: Git url for the OpenERP repository.
            * ``git-branch``: Branch name to use.        
            * ``git-commit``: Commit SHA-1 to use (override git-branch if defined).
* ``python-dependencies``: List of Python dependencies for this project (will be downloaded and installed in virtualenv by pip).
    * ``name``: The pip name of the Python library.
    * ``specifier``: The pip version constraint specifier.
    * ``options``: Add options for pip call.
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

	oebuild project.init
	
### Migration of configuration files

Configuration files for v1.7 projects will be migrated on first launch with v2.1.
However, as the python dependencies were not automatically installed with v1.7, you can specify default dependencies that will be integrated in every migrated project.

To do so, create a file named "default_python_deps.json" in the configuration directory ("~/.config/openerp-autobuild/") containing the required dependencies.
You can also add a specifier and some options (refer to ``python-dependencies`` in "Project Settings/Options").

Example :

	[
	    {"name": "phonenumbers"},
	    {"name": "six"},
	    {"name": "python-stdnum"},
	    {"name": "pyPdf"},
	    {"name": "BeautifulSoup"},
	    {"name": "pyth"},
	    {"name": "qrcode"},
	    {"name": "Pillow"},
	    {"name": "pyxb"}
	]

### Some examples

Run server and update _mymodule_ and _othermodule_

	oebuild run -u mymodule,othermodule

Run server in test mode on a new database named _my-custom-tests_ for continuous integration with all modules of your project  

	oebuild run.test --database=my-custom-tests --new-install --analyze -i

Build a fully runnable package  

	oebuild projet.assembly --include-odoo

See docs, man page or help for details

## Credits

Bluestar Solutions Sàrl  
Rue de la Maladière 23  
CH-2000 Neuchâtel

## Copyright

Copyright (C) 2012-2015 Bluestar Solutions Sàrl (<http://www.blues2.ch>).

## License

[GNU AFFERO GENERAL PUBLIC LICENSE, version 3](http://www.gnu.org/licenses/agpl-3.0.html)
