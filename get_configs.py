from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from getpass import getpass
from nornsible import InitNornsible, nornsible_task
from termcolor import colored
from nornir.core.task import Result
import os


def format_dir_vars(dir_var):
    if isinstance(dir_var, str) != True:
        raise ValueError(f"variable passed into 'format_dir_vars' function is not of type string")
    """
    Make sure environment variables which specify a directory are formatted
    correctly for use in script functions
    """
    if dir_var[-1] != '/':
        dir_var = dir_var + '/'
    
    return dir_var


def update_creds(nr):
    """
    Update username and password on nornir object at run time with user provided credentials
    User provided credentials will only be queried if username/password isn't set in inventory
    """
    for host, data in nr.inventory.hosts.items():
        if nr.inventory.hosts[host].username == None:
            username = input('Username: ')
            break

    for host, data in nr.inventory.hosts.items():
        if nr.inventory.hosts[host].password == None:
            password = getpass('Password: ')
            break    

    for host, data in nr.inventory.hosts.items():
        if nr.inventory.hosts[host].password:
            continue
        else:
            nr.inventory.hosts[host].password = password

    for host, data in nr.inventory.hosts.items():
        if nr.inventory.hosts[host].username:
            continue
        else:
            nr.inventory.hosts[host].username = username


@nornsible_task
def get_configs(task):
    """
    Get config and state information from devices according to commands specified
    in 'get_config_commands' nornir attribute
    """
    commands = task.host['get_config_commands']
    path = f"{CONFIGS_DIR}{task.host.name}/"
    get_config_results = []
    if os.path.isdir(path) == False:
        os.makedirs(path)
    for command in commands:
        result = task.run(task=netmiko_send_command, command_string=command)
        result = result[0].result
        filename = f"{path}{command}.ios"
        try:
            with open(filename, 'r') as f:
                current_contents = f.read()
            if result != current_contents:
                with open(filename, 'w') as f:
                    f.write(result)
                get_config_results.append({
                    'command': command,
                    'color': 'yellow',
                    'changed': True,
                })
            elif result == current_contents:
                get_config_results.append({
                    'command': command,
                    'color': 'green',
                    'changed': False,
                })
        except FileNotFoundError:
            with open(filename, 'w') as f:
                f.write(result)
            get_config_results.append({
                'command': command,
                'color': 'yellow',
                'changed': True,
            })

    task.host['get_config_results'] = get_config_results


@nornsible_task
def print_failed_hosts(task):
    """
    Print message indicatin any hosts on which config/state information 
    extraction failed.
    """
    print(colored(f'Failed to get config/state info from {task.host}', 'red'))


@nornsible_task
def print_get_cfg_results(task):
    """
    Print Get Config Results with colors indicating whether the file changed or not
    """
    results = task.host['get_config_results']
    print(colored(f"\n{task.host.name}", 'blue'))
    print('-' * 20)
    for result in results: 
        if result['changed'] == True:
            print(colored(f"{result['command']} -----> Changed: True", result['color']))
        if result['changed'] == False:
            print(colored(f"{result['command']} -----> Changed: False", result['color']))


def git_commit():
    """
    commit changes to a local git repo for analysis of changes between script executions
    """
    os.chdir(CONFIGS_DIR)
    os.system('git add --all > /dev/null')
    os.system("git commit -m 'Git Commit by Python getconfigs.py Script' > /dev/null")


NORNIR_CONFIG_FILE = os.environ['NORNIR_CONFIG_FILE']
CONFIGS_DIR = format_dir_vars(os.environ['CONFIGS_DIR'])


def main():
    # Initialize Nornir objects, filter with nornsible, remove delegate from nornsible returned hosts
    nr = InitNornir(config_file=NORNIR_CONFIG_FILE)
    nr = InitNornsible(nr)
    nr.inventory.hosts.pop('delegate')

    # Get credentials and assign to nornir inventory objects if they are not already specified
    update_creds(nr)

    # Get Configs from devices. Print Results
    nr.run(task=get_configs)
    nr.run(task=print_failed_hosts, on_good=False, on_failed=True, num_workers=1)
    nr.run(task=print_get_cfg_results, num_workers=1)

    # Commit to git
    git_commit()

if __name__ == "__main__":
    main()
