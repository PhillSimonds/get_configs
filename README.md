Get Configs
=======

This script is used to pull config and state info from networking devices and save them to a specified directory in an idempotent manner. The script will create a sub-directory with the Device's host name into which it will place files named according to the command run against the device. Afterwards, the device saves changes to GIT so that historic config/state data can be analyzed. 

- Nornir is used for inventory management and paralell execution
- Nornsible is used to parse Nornir inventory down to only those devices against which the script should be run
- Netmiko is used to pull device config and state information
- Getpass pulls in password information before authenticating to devices
- TermColor is used to print colored output to the screen. Yellow indicates file contents changed, Green indicates file contents did not change, Red indicates failure of the script to run against the host.

# How it Works

This script utilizes a few environment variables and nornir data elements

- The "NORNIR_CONFIG_FILE" environment variable must be sused to set the full location of the nornir config file
- The "CONFIGS_DIR" environment variable must be used to set the directory to which config/state info should be written on the local host
- The "get_config_commands" nornir inventory object attribute must contain a list of commands to be run against each device

# Supported Devices

Any device to which netmiko can initiate an SSH session with "netmiko_send_command" _should_ work. I've only tested the script on cisco devices.



