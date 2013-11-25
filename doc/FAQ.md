#Frequently Asked Questions

##Where openerp is installed ?
It is located in a workspace outside of the project. 
By default ~/openerp-autobuild/[your-project-name]/openerp

Take a look at your config file (~/.config/openerp-autobuild/oebuild_config-1.7.json) and locate the workspace key.

##Where is the code of my project dependencies ?
It is in a workspace outside of the project. 
By default : ~/openerp-autobuild/[your-project-name]/deps

Take a look at your config file (~/.config/openerp-autobuild/oebuild_config-1.7.json) and locate the workspace key.

##Is OpenERP autobuild 1.7 compatible with previous versions ?
Previous versions of OpenERP Autobuild configuration files are not compatible with the version 1.7 of OpenERP Autobuild.
However, dependencies may have previous configuration files but the transitive dependencies are not managed.

## Will OpenERP autobuild 1.7 be compatible with future versions
The version 1.7 is the first public release.
New release will remain compatible with this version.
