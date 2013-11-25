# Easy dependency management for OpenERP developers !

OpenERP Autobuild was created by Bluestar Solutions Sàrl an OpenERP partner who develops custom-made modules.

The main goals of OpenERP Autobuild are :

* Improve the collaboration in development teams.
* Permit the use of various VCS (currently git and bazaar).
* Enable the use of continuous integration solutions.

Inspired by solutions like composer (http://getcomposer.org) this tool is made for OpenERP modules developers. It manages the dependencies and the run goal of your project. By enabling the possibility to define precisely the revision of OpenERP you want to use in your project and by managing your custom dependencies and their transitive dependencies, it improves teams collaboration on projects ensuring developments and test are made on the same defined version.

The current version has the flowing execution goals :

* init : Initialize an empty OpenERP project with default configuration files.
* init-eclipse : Initialize an existing project as a Eclipse Pydev Project.
* run : Run OpenERP server with default parameters. Logs INFO level messages and up.
* debug : Same as run but with also logs DEBUG level messages.
* test : Run OpenERP server in test mode. In this mode, the server will use another database (named after your project's name) to load demo data and perform designated tests.
* assembly : Build a package with your custom add ons and their dependencies in order to deploy the application.
