# NovaColumnV2

Welcome to NovaColumnV2!
This is an updated version of the original (and quite terrible) [NovaColumn](https://github.com/PaddockBux/NovaColumn).

## What's this?

NovaColumnV2 is an educational tool that scans the internet for Minecraft servers and queries them for their status. After pinging, the data is then taken from the server and saved into the database for historical logging.\
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

Clone the repo using `git clone https://github.com/PaddockBux/NovaColumnV2` and then run the script using `python3 ncv2.py`.

## Usage

Running the script once will create the required database connection configuration file if it is missing.

Using NCV2 is quite simple, included in the script is a help page:

```Text
usage: ncv2.py [-h] [-u] [-v] [-t THREADS] [-m TIMEOUT] [-e] [-c] [file]

               _   __                 ______      __                    _    _____ 
              / | / /___ _   ______ _/ ____/___  / /_  ______ ___  ____| |  / /__ \
             /  |/ / __ \ | / / __ `/ /   / __ \/ / / / / __ `__ \/ __ \ | / /__/ /
            / /|  / /_/ / |/ / /_/ / /___/ /_/ / / /_/ / / / / / / / / / |/ // __/ 
           /_/ |_/\____/|___/\__,_/\____/\____/_/\__,_/_/ /_/ /_/_/ /_/|___//____/ 
                                        NovaColumn V2
          Programmed by & main ideas guy: GoGreek    ::    Co-ideas guy: Draxillian

       Fair warning, calling the update function will take a while on large databases!

positional arguments:
  file                  The path to the .json file to be parsed.

options:
  -h, --help            show this help message and exit
  -u, --update          Ping/Update the current servers in the database. (does not require a file)
  -v, --verbose         Enable verbose mode to print detailed logs.
  -t THREADS, --threads THREADS
                        The amount of threads to process the file with. (4 default)
  -m TIMEOUT, --timeout TIMEOUT
                        The timeout speed for the servers, read the README for more info. (0.3 default)
  -e, --external        Used for when the database is not on the same machine. (only applies for --update)
  -c, --verify          Verify all playernames in the database. (does not require a file)

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

Pull requests must be clear and concise.\
If you want to add a new feature, please open an issue first to discuss. Issues with no clarification or reason (add x because yes) will be closed.

## License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](./LICENSE) file for details.
