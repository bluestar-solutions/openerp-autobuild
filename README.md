# Autobuild for OpenERP

Autobuild for OpenERP is an utility script designed to simply configure, debug, deploy and run customized OpenERP applications.

## Installation

### From Ubuntu PPA

	sudo add-apt-repository ppa:bluestar-dev-team/openerp-autobuild
	sudo apt-get update`
	sudo apt-get install openerp-autobuild

If you want to install an older version:

	sudo apt-get install openerp-autobuild-X.X # With X.X the desired version

## Configuration

### User Settings

You can find your user setting under ~/.config/openerp-autobuild/oebuild_config-X.X.json, with X.X the target version of the settings.

#### Commented Exemple

	{
		# The workspace folder, where openerp-autobuild will pull 
		# all the dependencies needed by your projects :
		"workspace": "~/openerp-autobuild",

		# A list of project configuration name used to override 
		# the project default configuration, used to specify 
		# custom dependency source or version :
		"custom-configuration-files": ["bluestar", "herve.martinet"],

		"openerp": [
			{
				# The url to find official OpenERP trunk series :
				"serie": "trunk",
				"server": "lp:openobject-server",
				"addons": "lp:openobject-addons",
				"web": "lp:openerp-web"
			},
			{ 
				# The url to find official OpenERP 6.0 series :
				"serie": "6.0",
				"server": "lp:openobject-server/6.0",
				"addons": "lp:openobject-addons/6.0",
				"web": "lp:openerp-web/6.0"
			},
			{
				# The url to find official OpenERP 6.1 series :
				"serie": "6.1",
				"server": "lp:openobject-server/6.1",
				"addons": "lp:openobject-addons/6.1",
				"web": "lp:openerp-web/6.1"
			},
			{ 
				# The url to find official OpenERP 7.0 series. Here with custom url
				# if you have a local bazaar mirror of OpenERP serie 7.0 to speed up operations :
				"serie": "7.0",
				"server": "bzr://my-bzr-server/openerp-7.0-default-server",
				"addons": "bzr://my-bzr-server/openerp-7.0-default-addons",
				"web": "bzr://my-bzr-server/openerp-7.0-default-web"
			},
			{
				# The url to find a custom OpenERP 7.0 series with modified web :
				"serie": "7.0-hacked-by-me",
				"server": "bzr://my-bzr-server/openerp-7.0-default-server",
				"addons": "bzr://my-bzr-server/openerp-7.0-default-addons",
				"web": "bzr://my-bzr-server/openerp-7.0-hacked-by-me-web"
			}
		],

		# The default serie to use for new projects :
		"default-serie": "7.0",

		# Your PostgreSQL settings for OpenERP :
		"database": {
			"host": "localhost",
			"port": "5432",
			"user": "openerp",
			"password": "openerp"
		}
	}

### Project Settings

The default project settings are in oebuild.conf, located at the root of the concerned project. This file can be overridden by every oebuild_*.conf, if * is defined in your user settings custom-configuration-files list.

For exemple if you have ["my.a", "my.c"] in your user settings and oebuild.conf, oebuild_my.a.conf, oebuild_my.b.conf, oebuild_my.c.conf in your project. All the dependencies defined in oebuild_my.a.conf will replace dependencies defined in oebuild.conf with the same name. Then the same operation will be realized with oebuild_my.c.conf on the resulted dependency list. oebuild_my.b.conf will be ignored because it is not listed in your user configuration.

#### Commented Exemple

oebuild.conf:

	{
		# The target version of OpenERP Autobuild :
		"oebuild-version": "X.X",

		# The project name :
		"project": "my-openerp-addons",

		"openerp": {
			"serie": "7.0",
			"server": {
				# Specific bazaar revision to use for server :
				"bzr-rev": "4898"
			},
			"addons": {
				# Specific bazaar revision to use for server :
				"bzr-rev": "8875"
			},
			# No bazaar revision specified for web, use the last one.
		},

		# If the project source code will be public, all url of dependency should be too :
		"dependencies": [{ 
			# The dependency name :
			"name": "another-addons-a",
			"source": {
				"scm": "bzr",

				# URL of a bazaar branch :
				"url": "lp:~team-a/another-addons-a/7.0.1.0"
			}
		},{
			"name": "another-addons-b",
			"source": {
				"scm": "bzr",

				# URL of a launchpad serie :
				"url": "lp:another-addons-b/7.0"
				
				# Specific bzr revision to use. Optionnal, default last revision :
				"bzr-rev": "1234"
			}
		},{ 
			# A git dependency :
			"name": "another-addons-c",
			"source": {
				"scm": "git",
				"url": "ssh://git@github.com:user/another-addons-c.git",

				# Specific git branch to use. Optionnal, default "master" :
				"git-branch": "a-branch" 
			}
		}]
	}

oebuild-custom.conf :

	{
		"oebuild-version": "X.X",
		"project": "my-openerp-addons",
		"openerp": {
			"serie": "7.0",
			"addons": {
				# Specific bazaar revision to use for addons, will replace 
				# the one defined in oebuild.conf if this file is used :
				"bzr-rev": "2222"
			},
			"web": {
				# Specific bazaar revision to use for web :
				"bzr-rev": "1111"
			},
		},
		"dependencies": [{
			"name": "another-addons-b",
			"source": {
				"scm": "bzr",

				# Use a local mirror to get another-addons-b :
				"url": "bzr://my-bzr-server/another-addons-b-7.0"
				
				# Specific bzr revision to use. Optionnal, default last revision ;
				"bzr-rev": "1234"
			}
		},{
			"name": "another-addons-c",
			"source": {
				"scm": "git",
				"url": "ssh://git@github.com:user/another-addons-c.git",
				
				# Take anothe branch, will replace the one defined in oebuild.conf if this file is used :
				"git-branch": "b-branch"
			}
		}]

		# another-addons-b is not defined here, source defined in oebuild.conf will be used for it.
	}

### OpenERP Settings

With OpenERP Autobuild, OpenERP will use the file ".openerp-dev-default" located at the root of the project to get OpenERP run settings.

#### Exemple

	[options]
	admin_passwd = admin
	csv_internal_sep = ,
	db_maxconn = 64
	db_name = False
	db_template = template1
	dbfilter = .*
	debug_mode = False
	demo = {}
	email_from = False
	import_partial = 
	limit_memory_hard = 805306368
	limit_memory_soft = 671088640
	limit_request = 8192
	limit_time_cpu = 60
	limit_time_real = 60
	list_db = True
	log_handler = :INFO 
	log_level = info
	logfile = None
	login_message = False
	logrotate = True
	max_cron_threads = 4
	netrpc = True
	netrpc_interface = 
	netrpc_port = 8070
	osv_memory_age_limit = 1.0
	osv_memory_count_limit = False
	pg_path = None
	pidfile = None
	proxy_mode = False
	reportgz = False
	secure_cert_file = server.cert
	secure_pkey_file = server.pkey
	server_wide_modules = None
	smtp_password = False
	smtp_port = 25
	smtp_server = localhost
	smtp_ssl = False
	smtp_user = False
	static_http_document_root = None
	static_http_enable = False
	static_http_url_prefix = None
	syslog = False
	test_commit = False
	test_enable = False
	test_file = False
	test_report_directory = False
	timezone = False
	translate_modules = ['all']
	unaccent = False
	without_demo = False
	workers = 0
	xmlrpc = True
	xmlrpc_interface = 
	xmlrpc_port = 8069
	xmlrpcs = True
	xmlrpcs_interface = 
	xmlrpcs_port = 8071

### Goals

* **run** : Run OpenERP server with default parameters. Logs only INFO level messages.
* **debug** : Same as run but also logs DEBUG level messages.
* **test** : Run OpenERP server in test mode. In this mode, the server will use another database (named after your project's name) to load demo data and perform designated tests.
* **assembly** : Build a package with your custom addons and their dependencies in order to deploy the application.
* **init-eclipse** : Initialize an existing project as a _Eclipse Pydev Project_

### Shared parameters

* **-m**, **--modules** : Specify which custom module to load. If omitted, all custom modules will be loaded.
* **-p**, **--tcp-port** : TCP port of the server (default:8069).

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

[GNU AFFERO GENERAL PUBLIC LICENSE, version 3](http://www.gnu.org/licenses/agpl-3.0.html)
