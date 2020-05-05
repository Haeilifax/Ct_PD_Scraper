# Ct_PD_Scraper

A small tool I'm developing to automatically scrape the Republican American police blotter blog posts. It will automatically scrape every blotter off the first page of <https://www.rep-am.com/category/local/records/police/>. These blotters are then separated into arrests and entered into a database for easy searching. A Republican American online login is required.

## Usage

In order to use this script properly, you must create a .env file in the root directory and write your login information as specified in the .env section below. Then, simply run either cli.py (if using the python interface), or PoliceScraper.exe (if using the executable interface). The rest should work automatically. This script should be run in the same location as config.toml, .env, and the data folder. By modifying the config file (using a text editor), you can change the relative paths to the data folder and .env file. Please report any bugs.

### MySQL caveats

The above Usage section holds, but modification of the config file (config.toml) is necessary for use with MySQL. In particular, the value of database.inserter must be "mysql", and user, database, and password in database.config.mysql must be set to appropriate values. Inside the given database, it is expected that there be at least two tables, person and content (definitions given below). Other options in the config.toml file exist to override any defaults in the mysqlclient connector; more information can be found at https://mysqlclient.readthedocs.io/user_guide.html

#### Table "person"

CREATE TABLE `person` ( `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT, `first_name` varchar(64) DEFAULT NULL, `last_name` varchar(64) DEFAULT NULL, UNIQUE KEY `id` (`id`));

#### Table "content"

CREATE TABLE `content` ( `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT, `person_id` bigint(20) unsigned DEFAULT NULL, `pdcity` varchar(16) DEFAULT NULL, `content` text, `date` date DEFAULT NULL, UNIQUE KEY `id` (`id`), KEY `person_id` (`person_id`), CONSTRAINT `content_ibfk_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`id`) ON DELETE CASCADE);

## Setting up scheduled runs (Windows)

Scheduled runs of this scraper can be most easily done with the .exe file. The files should be of version 0.2.0 or later, for proper behavior as a background task. Open the Task Scheduler by pressing Win+R and typing "taskschd.msc". Right-click the blank space (or click Action in the menu bar) and click on "Create New Task..." (or "Create Task"). Name the task something like "ScrapePolice", and then click the Triggers tab. Select options that make sense for you, and then click the Actions tab. Click "New...", and browse for the executable in your computer. Then, very significantly, make sure the "Start in" location is the directory which contains your config.toml file (and should also contain your .env file and data folder by default). Look through the Conditions tab and modify to your pleasing, then click the Settings tab. I would suggest ticking the "Run task as soon as possible after a scheduled start is missed" box. Then, click the "Ok" button and you should be set up to scrape daily.

## Setting up scheduled runs (Linux)

Make a cron job. Tutorials are available online, or through "man crontab". Ensure that your job is in the appropriate python environment, with all dependencies installed.

### The .env file

A .env file can be created by opening a text editor and writing the following, filling in any information with your relevant credentials, then saving as .env:  

log = "\<enter your username for rep-am.com here>"  
pwd = "\<enter your password for rep-am.com here>"  
submit = "Log+In"  
redirect_to = "https://www.rep-am.com/wp-admin/"  
testcookie = "1"

Ensure that all values on the righthand side of the equals sign are surrounded by quote marks. These values will be parsed by the script and used to log the session in. Also ensure that the file is named simply _.env_ , with no extension or other characters.

### The config.toml file

The config file is written in TOML (more information at <https://github.com/toml-lang/toml>). It shouldn't need to be changed, but if you have a non-standard setup (e.g., a data folder in a different location), modifying it may be essential. Going header by header, we have:

#### [project]

Basic information about the project: name, a brief description, version number, date last updated, author name

#### [data]

One item, the relative path to the data folder from the config file. Change this if your data folder is in a non-standard location.

#### [env]

As above, a single relative path to the .env file from the config file. Change this if your .env file is in a non-standard location.

#### [prev_links]

A single relative path from the _data folder_ to the json file which stores the already scraped links.

#### [login]

Contains the url to POST the login request to, as well as a subtable of the headers used to mimic a Firefox browser during login.

#### [session]

Contains the base url to scrape links to blotters from. This can be changed to scrape links off older pages. The base_pages setting is unimplemented. This header also contains the headers to mimic a Firefox browser during the session.

#### [database]

Contains the type of inserter (i.e. database) to use. Contains configuration settings for databases under database.config.{type_of_database}.

##### [database.config.sqlite]

Contains the path of the database as the value of "database".

##### [database.config.mysql]

Contains 3 sections: the first section, of user, database, and password, require values to use the MySQL database with this scraper. Sections 2 and 3 are provided to expose the arguments to mysqlclient's connect function. Only modify these if you know what you are doing.

#### [cleaning]

Contains the type of cleaner: any option besides basic will be non-functional.
