# NovaColumnV2

NovaColumnV2 is an educational tool that uses [masscan](https://github.com/robertdavidgraham/masscan) to scan the internet for Minecraft servers.\
We have created a web UI that our main [website](https://novacolumn.com) provides as a demo, you can find the repo [here](https://github.com/PaddockBux/NovaColumn-WebUI).

## Disclaimers

NovaColumn is provided as-is and does not contain any warranty.\
This is a very dangerous tool that can get your internet blocked if abused.\
We do not take responsibility for any damages caused by using this tool.

## Prerequisites

NovaColumn requires Python3.8+ and a MariaDB server with a user that requires the following privileges:

- SELECT
- INSERT
- UPDATE
- CREATE
- INDEX

The script will create the necessary tables and columns for you if they do not exist.

Python libraries are also supplied in the requirements.txt file. To install, run either `pip install -r requirements.txt` or `python -m pip install -r requirements.txt`.

## Installation

Clone the repo using `git clone https://github.com/PaddockBux/NovaColumnV2` and then run the script in the adjacent directory using `python ncv2.py`.

## Usage

NCV2 drops a config file on first run (unless you manually pass database credentials using the arguments). Just simply run the script and it will drop a file named `novacolumn.conf` in the same directory. Included is the entries for credentials used to interface with the MariaDB server.

After creating and filling out the configuration file, you're ready to use NCV2.\
To use NCV2, run masscan with a json output (`-oJ <filename>.json`). When masscan is completed run NCV2 with the output file: `python ncv2.py <filename>.json`.

Information about arguments are shown when the `-h` argument is added.

```Text
usage: ncv2.py [-h] [-u] [-v] [-t THREADS] [-m TIMEOUT] [-e] [-c] [-a] [--dbusername DBUSERNAME] [--dbpassword DBPASSWORD] [--dbhost DBHOST] [--dbport DBPORT] [--dbname DBNAME] [file]

               _   __                 ______      __                    _    _____
              / | / /___ _   ______ _/ ____/___  / /_  ______ ___  ____| |  / /__ \
             /  |/ / __ \ | / / __ `/ /   / __ \/ / / / / __ `__ \/ __ \ | / /__/ /
            / /|  / /_/ / |/ / /_/ / /___/ /_/ / / /_/ / / / / / / / / / |/ // __/
           /_/ |_/\____/|___/\__,_/\____/\____/_/\__,_/_/ /_/ /_/_/ /_/|___//____/
                                        NovaColumn V2
          Programmed by & main ideas guy: GoGreek    ::    Co-ideas guy: Draxillian

       Fair warning, calling the update function will take a while on large databases!

positional arguments:
  file                  the path to the .json file to be parsed.

options:
  -h, --help            show this help message and exit
  -u, --update          ping/Update the current servers in the database. (does not require a file)
  -v, --verbose         enable verbose mode to print detailed logs.
  -t THREADS, --threads THREADS
                        the amount of threads to process the file with. (4 default)
  -m TIMEOUT, --timeout TIMEOUT
                        the timeout speed for the servers, read the README for more info. (0.3 default)
  -e, --external        used for when the database is not on the same machine. (only applies for --update)
  -c, --verify          verify all playernames in the database. (does not require a file)
  -a, --altapi          verify using the official Mojang API instead of Mowojang. (only applies for --verify)
  --dbusername DBUSERNAME
                        pass database username via argument.
  --dbpassword DBPASSWORD
                        pass database password via argument.
  --dbhost DBHOST       pass database host via argument. (default localhost)
  --dbport DBPORT       pass database port via argument. (default 3306)
  --dbname DBNAME       pass database name via argument. (default 'novacolumn')

Example usage:
Verbose
    nc2 -v input.json
Update the database
    nc2 -u
Use multiple threads
    nc2 -t 10 input.json
Change timeout & threads
    nc2 -m 2.3 -t 10 input.json

For more information, check the README file.
```

## Contributing

Pull requests must be clear about what's added.\
If you want to add a new feature, please open an issue or send a message in our Discord server channel #suggestions to discuss. Issues with no clarification or reason (add x because yes) will be rejected.

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](./LICENSE) file for details.

## Contact

If you need help with utilizing NCV2 or just want to see plans and updates, join our [Discord server](https://discord.gg/FtSqu7FzHJ).
