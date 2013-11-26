# Getting started

In this quick start guide you will learn : 

- How to install openerp autobuild
- How to create and run your project
- How to set the revision of OpeneERP
- How to add dependencies to your project

If you want to go further, you can read more about all the options here [README.md].

### Install from Ubuntu PPA
	
	sudo add-apt-repository ppa:bluestar-dev-team/openerp-autobuild
	sudo apt-get update
	sudo apt-get install openerp-autobuild

### Configure

Open your main configuration file ~/.config/openerp-autobuild/oebuild_config.json and locate the database configuration :

	"database": {
        "host": "localhost",
        "port": "5432",
        "user": "openerp",
        "password": "openerp"
    }

Change it according to your PostgreSQL settings. 

This configuration file contains your settings for all the projects.
Discover the whole configuration in the read me file located here [README.md].

### Initialise and Run a project
Creating a new project is easy as :

Create a new folder and move into it

	mkdir openerp-myproject
	cd openerp-myproject

Run __oebuild init__ to create the project

	oebuild init

Run your new OpenERP project

	oebuild run

Wait until you see this log line : ... HTTP service (werkzeug) running on 0.0.0.0:8069
You may now connect to a running openerp instance at http://localhost:8069/.

### Create your own module

You have now everything ready to create your own modules.

oebuild has no option to create modules automatically (maybe in a future version).
You have to create a new folder for your module at the root of your project folder 
and create your module code inside as any OpenERP module.

Once your module is ready to run, simply do a 

	oebuild run

It will add your module to the addons path and update it if necessary.

### Specify the revision of openerp for your project

oebuild takes by default the last version of each OpenERP components (server, addons, web).
It may download a version that doesn't run. 
If it's the case or if you need a specific version of openerp you have to specify the revision number of each components.

Take a look at the runbot page to get the last revision that passes the tests : http://runbot.openerp.com/

Each oebuild project has an oebuild.conf file at the root of the project. 
It is the main configuration file for your project.

Open it and locate the openerp section. Add the server, addons and web keys and set the revision as follow :

    "openerp": {
        "serie": "7.0",
        "server": {
                "bzr-rev": "5071"
            },
        "addons": {
                "bzr-rev": "9431"
            },
        "web": {
                "bzr-rev": "4027"
        }

### Add a new dependency

As an example, let say your project will depends on the Jira Module made by Bluestar Solutions 
available on launchpad (https//launchpad.net/bss-jira-addons)

Edit your project configuration file oebuild.conf located at the root of your project. 
Locate the dependencies key and add a new dependency as follow :

	"dependencies": [
		{
		 "name": "bss-jira-addons",
		 "source": {
                 	"scm": "bzr",
	                "url": "lp:bss-jira-addons"
        	 	}
        	}
      	]

Run openerp autobuild and it will download for you the bss-jira-addons and add it to the addons path. 

If the dependency is also made with oebuild, it will download the dependencies of the dependency (transitive dependencies).
In this case bss-jira-addons depends on bss-webservice-addons.

__You can also add dependencies that are not made with oebuild but there is not transitive dependencies support__

oebuild supports also dependencies that are managed with git : 

	"dependencies": [
		{
		 "name": "not_functionnal_demo_addon",
		 "source": {
                 	"scm": "git",
                        "url": "ssh://git@github.com:user/another-addons-c.git",
        	 	}
        	}
      	]
