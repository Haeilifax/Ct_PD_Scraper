# Ct_PD_Scraper

A small tool I'm developing to automatically scrape the Republican American police blotter blog posts. It will automatically scrape every blotter off the first page of <https://www.rep-am.com/category/local/records/police/>. These blotters are then separated into arrests and entered into a database for easy searching. A Republican American online login is required.

## Usage:

In order to use this script properly, you must create a .env file in the root directory and write your login information as specified in the .env section below. Then, simply run either cli.py (if using the python interface), or PoliceScraper.exe (if using the executable interface). The rest should work automatically. This script should be run in the same location as config.toml, .env, and the data folder. By modifying the config file (using a text editor), you can change the relative paths to the data folder and .env file. Please report any bugs.

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

##### [project]

Basic information about the project: name, a brief description, version number, date last updated, author name

##### [data]

One item, the relative path to the data folder from the config file. Change this if your data folder is in a non-standard location.

##### [env]

As above, a single relative path to the .env file from the config file. Change this if your .env file is in a non-standard location.

##### [login]

Contains the url to POST the login request to, as well as a subtable of the headers used to mimic a Firefox browser during login.

##### [session]

Contains the base url to scrape links to blotters from. This can be changed to scrape links off older pages. The base_pages setting is unimplemented. This header also contains the headers to mimic a Firefox browser during the session.

##### [database]

Contains the path of the database relative to the data folder. If the database is in the data folder, only the file name of the database is required. Also contains the type of inserter: any option besides basic will be non-functional.

##### [cleaning]

Contains the type of cleaner: any option besides basic will be non-functional.