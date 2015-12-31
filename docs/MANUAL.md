openerp-autobuild -- build and run Odoo/OpenERP projects 
========================================================

## SYNOPSIS

`openerp-autobuild` [--version] [--help]  
`oebuild` [--version] [--help]  
`openerp-autobuild` <goal> [--help]  ...  
`oebuild` <goal> [--help]  ...

## DESCRIPTION

A tool to build and run Odoo/OpenERP projects.

The main goals of OpenERP Autobuild are:

* Improve the collaboration in development teams.
* Permit the use of various VCS (currently git and bazaar).
* Enable the use of continuous integration solutions.

Inspired by solutions like composer (http://getcomposer.org) this tool is made
for OpenERP modules developers. It manages the dependencies and the run goal
of your project. By enabling the possibility to define precisely the revision
of OpenERP you want to use in your project and by managing your custom
dependencies and their transitive dependencies, it improves teams
collaboration on projects ensuring developments and test are made
on the same defined version.

## OPTIONS

* `-v`, `--version`:
    Prints openerp-autobuild version.
* `-h`, `--help`:
    Prints the synopsis and the list of goals.

## GOALS
    
* `run`:
    Run Odoo server normally.
* `run.test`:
    Run Odoo server, perform tests, stop the server and
    display tests results.
* `project.init`:
    Initialize an empty Odoo project.
* `project.version`:
    Set the version of all project modules.
* `project.assembly`:
    Prepare all files to deploy in target folder.
* `module.create`:
    Create a new module.
* `eclipse.init`:
    Initialize an Eclipse PyDev project.

## GOALS OPTIONS

### run

`openerp-autobuild` run [-h] [-A [<path>]] [-u [all|<module1>[,<module2>…]]]
[-i [all|<module1>[,<module2>…]]] [-l] [-d <database>] [-a]  
`oebuild` run [-h] [-A [<path>]] [-u [all|<module1>[,<module2>…]]]
[-i [all|<module1>[,<module2>…]]] [-l] [-d <database>] [-a]


* `-h`, `--help`:
    Prints usage and options for the goal.
* `-d` <database>, `--database`=<database>:
    Database used when installing or updating modules.
* `-u` [all|<module1>[,<module2>...]], `--update`=[all|<module1>[,<module2>...]]:
    Modules to install. Don't specify any module to use
    the module list of the current project. `--database` is
    required.
* `-i` [all|<module1>[,<module2>...]], `--init`=[all|<module1>[,<module2>...]]:
    Modules to update. Don't specify any module to use the
    module list of the current project. `--database` is
    required.
* `-a`, `--auto-reload`:
    Enable auto-reloading of python files and xml files
    without having to restart the server. Requires
    pyinotify. Available since Odoo version 8.0
* `-A` [<path>], `--alternate-config`=[<path>]:
    Use an alternate directory to find configuration files
    instead of /etc and /home/user (for development
    purpose). Don't specify <path> to use './devconf' with
    supplied files.
* `-l`, `--local`:
    Bypass remote updates checks and try to launch with
    last parameters.

### run.test

* `-h`, `--help`:
    Prints usage and options for the goal.
* `-d` <database>, `--database`=<database>:
    Database name for tests.Use autobuild_{PROJECT_NAME} if not specified.
* `-u` [all|<module1>[,<module2>...]], `--update`=[all|<module1>[,<module2>...]]:
    Modules to install. Don't specify any module to use
    the module list of the current project. `--database` is
    required.
* `-i` [all|<module1>[,<module2>...]], `--init`=[all|<module1>[,<module2>...]]:
    Modules to update. Don't specify any module to use the
    module list of the current project. `--database` is
    required.
* `-A` [<path>], `--alternate-config`=[<path>]:
    Use an alternate directory to find configuration files
    instead of /etc and /home/user (for development
    purpose). Don't specify <path> to use './devconf' with
    supplied files.
* `-l`, `--local`:
    Bypass remote updates checks and try to launch with
    last parameters.
* `-c`, `--test-commit`:
    Commit test results in DB.
* `-n`, `--new-install`:
     Force new install. This will delete the database if it exists.
* `-a`, `--analyze`:
    Analyze log and stop Odoo, exit with status 0 if all
    test successfully pass, 1 otherwise. Used for
    continuous integration.
* `-C`, `--continue`:
    Continue running Odoo server when tests are done.
* `-D`, `--drop-database`:
    Drop used database before exiting.

### project.init

* `-h`, `--help`:
    Prints usage and options for the goal.
* `-A` [<path>], `--alternate-config`=[<path>]:
    Use an alternate directory to find configuration files
    instead of /etc and /home/user (for development
    purpose). Don't specify <path> to use './devconf' with
    supplied files.
* `-l`, `--local`:
    Bypass remote updates checks and try to launch with
    last parameters.
    
### project.version

* `-h`, `--help`:
    Prints usage and options for the goal.
* `-n` [<version>], `--new-version`=[<version>]:
    The modules new version.
* `-A` [<path>], `--alternate-config`=[<path>]:
    Use an alternate directory to find configuration files
    instead of /etc and /home/user (for development
    purpose). Don't specify <path> to use './devconf' with
    supplied files.
* `-l`, `--local`:
    Bypass remote updates checks and try to launch with
    last parameters.

### project.assembly

* `-h`, `--help`:
    Prints usage and options for the goal.
* `-i`, `--include-odoo`:
    Include Odoo/OpenERP in target.
* `-A` [<path>], `--alternate-config`=[<path>]:
    Use an alternate directory to find configuration files
    instead of /etc and /home/user (for development
    purpose). Don't specify <path> to use './devconf' with
    supplied files.
* `-l`, `--local`:
    Bypass remote updates checks and try to launch with
    last parameters.
    
### module.create

* `-h`, `--help`:
    Prints usage and options for the goal.
* `-L` [<long-name>], `--long-name`=[<long-name>]:
    The module long name.
* `-c` [<category>], `--category`=[<category>]:
    The module long name.
* `-A` [<path>], `--alternate-config`=[<path>]:
    Use an alternate directory to find configuration files
    instead of /etc and /home/user (for development
    purpose). Don't specify <path> to use './devconf' with
    supplied files.
* `-l`, `--local`:
    Bypass remote updates checks and try to launch with
    last parameters.
    
### eclipse.init

* `-h`, `--help`:
    Prints usage and options for the goal.
* `-A` [<path>], `--alternate-config`=[<path>]:
    Use an alternate directory to find configuration files
    instead of /etc and /home/user (for development
    purpose). Don't specify <path> to use './devconf' with
    supplied files.
* `-l`, `--local`:
    Bypass remote updates checks and try to launch with
    last parameters.
    
## FAQ

### Where Odoo/OpenERP is installed ?

It is located in a workspace outside of the project. 
By default /var/oebuild/[your-project-name]/openerp

You can override the default value (~/tec/oebuild_config.json) in your
user configuration file (~/.config/openerp-autobuild/oebuild_config.json).

### Where is the code of my project dependencies ?

It is in a workspace outside of the project. 
By default : /var/oebuild/[your-project-name]/deps

You can override the default value (~/tec/oebuild_config.json) in your
user configuration file (~/.config/openerp-autobuild/oebuild_config.json).

### Is OpenERP Autobuild compatible with previous versions ?

OpenERP Autobuild configuration files are not compatible with previous version,
but OpenERP Autobuild will automatically update your project configuration
files. If dependencies have previous configuration files autobuild will
update these in the workspace to use it.
    
## AUTHORS

OpenERP Autobuild was started an maintained by Bluestar Solutions Sàrl
(<http://www.blues2.ch>), an Odoo partner who develops custom-made modules.

Project and sources: <https://github.com/bluestar-solutions/openerp-autobuild>

## COPYRIGHT

Copyright (C) 2012-2015 Bluestar Solutions Sàrl (<http://www.blues2.ch>).
Released under GNU AGPLv3.




