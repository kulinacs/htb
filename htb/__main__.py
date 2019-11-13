"""
A command line utility for interacting with the Hack the Box API
"""
from . import HTB
import argparse
from argparse import ArgumentParser
from pathlib import Path
import configparser
import sys
from tabulate import tabulate

apiKey = None
lab = None

def init_api(apiKey):
    global api
    api = HTB(apiKey)

def init_config():
    """
    Initialize the configuration directory and files. This will touch the file whether it already exists or not.
    """
    global config, configfile, configdir

    config = configparser.ConfigParser()

    configdir = Path.home().joinpath(".config/htb")
    configdir.mkdir(parents=True, exist_ok=True)

    configfile = configdir.joinpath('htb.conf')
    configfile.touch()

def write_config():
    """
    Write the config object to the config file.
    """
    with configfile.open('w') as f:
        config.write(f)

def load_config():
    """
    Load the config object from the config file.
    """
    global configfile, config, apiKey, lab
    init_config()
    config.read(configfile)
    if "Auth" not in config.sections():
        config['Auth'] = {'apiKey': '', 'lab':'free'}
        write_config()
    apiKey = config['Auth'].get('apiKey')
    lab = config['Auth'].get('lab')

def print_config():
    print("\nCurrent Configuration")
    for section in config.sections():
        for key, val in config.items(section):
            print(f"\t{key}:\t{val}")
    print("\n")

def load_machines():
    """
    Load the machines, and the users owned machines 
    and store them globally, since everything uses them.
    """
    global machines
    def add_owns(machine):
        """
        Adds whether the user has owned user or root on this box yet or not.
        """
        machine['owned_user'] = owns_dict[machine['id']]['owned_user'] if machine['id'] in owns_dict else False
        machine['owned_root'] = owns_dict[machine['id']]['owned_root'] if machine['id'] in owns_dict else False
        machine['active'] = not machine['retired']
        return machine
    
    owns = api.get_owns()
    owns_dict = dict(zip([m['id'] for m in owns], owns))
    machines = list(map(add_owns, api.get_machines()))

def get_id(name):
    """
    A helper function to translate a name into the machine's 
    id number since thats what the api expects.
    """
    for machine in machines:
        if machine['name'].lower() == name.lower():
            return machine['id']
    return None

def format_value(val):
    """
    A helper function to format fields for table output.
    Converts nested dicts into multilist strings.
    """
    if isinstance(val, dict):
        return "\n".join([ f"{k}: {val[k]}" for k in val.keys()])
    return val

def print_machine(machine, fields=None):
    """
    Print a machine and all of the requested fields.
    In the future we will implement more formatting options.
    """
    fields = fields or machine.keys()
    vals = list(map(lambda x: format_value(machine[x]), fields))
    items = list(zip(fields, vals))
    print(tabulate(items, tablefmt="fancy_grid"))

def print_machine_list(machines, fields=["id", "name", "os", "rating", "owned_user", "owned_root", "active"]):
    
    reduced_machines = list(map(lambda machine: [ format_value(machine[field]) for field in fields], machines))
    print(tabulate(reduced_machines,headers=fields, tablefmt="fancy_grid"))

def do_config(args):
    """
    Handle configuration commands.
    Currently this only includes setting or retrieving the current api key.
    """
    global apiKey, lab, config
    config['Auth']['apiKey'] = args.apiKey
    config['Auth']['lab'] = args.lab
    write_config()
    apiKey = args.apiKey
    
    print_config()


def do_list(args):
    """
    Handle the list command.
    Current filters limited to --retired and --incomplete, 
    but more will hopefully be implemented in the near future.
    """
    global machines
    def filter_machine(machine):
        machine_retired = machine['retired']
        machine_incomplete = not machine['owned_user'] or not machine['owned_root']

        return (machine_incomplete or not args.incomplete) and (not machine_retired or args.retired)
    if args.all_fields:
        fields = machines[0].keys() if len(machines) > 0 else []
    else:
        fields = args.fields or ["id", "name", "os", "rating", "owned_user", "owned_root", "active"]

    filtered_machines = list(filter(filter_machine, machines))
    if args.quiet:
        print(args.row_separator.join([ args.separator.join([ str(machine[field]) for field in fields]) for machine in filtered_machines]))
    else:
        print_machine_list(filtered_machines, fields)

def do_info(args):
    """
    Handle the info command.
    Currently only prints out the values of the specified box.
    Eventually, this should include options to better format the output.
    """
    machine = api.get_machine(get_id(args.box))
    if args.all_fields:
        fields = machine.keys()
    else:
        fields = args.fields or machine.keys()
    if args.quiet:
        vals = [ str(machine[f]) for f in fields ]
        print(args.separator.join(vals))
    else:
        print_machine(machine, fields)


def do_spawn(args):
    """
    Handle the spawn command.
    This will try to spawn the specified box.
    This command will fail if the user already has a box that is 
    assigned to them. Make sure to terminate any boxes assigned to you 
    before running this.
    """
    if lab == "free":
        print("Free users cannot spawn machines. Please use reset instead.")
        sys.exit(1)
    print(f"Attempting to spawn {args.box.capitalize()}. This request often takes ~30 seconds, so be patient please...")
    res, message = api.spawn_machine(get_id(args.box))
    sys.exit(res)

def do_own(args):
    """
    Handle the own command.
    This will try to own the specified box with the specified flag 
    and the difficulty rating passed.
    NOTE: The difficulty rating is mandatory.
    """
    flag = args.flag
    diff = args.difficulty
    print(f"Attempting to own {args.box.capitalize()} with flag: {flag} and rating: {diff}/9...")
    res, message = api.own_machine(get_id(args.box), flag, diff*10)
    print(message)
    sys.exit(res)

def do_terminate(args):
    """
    Handle the terminate command.
    This will attempt to terminate the specified box.
    NOTE: This command can take up to a couple minutes to successfully terminate
    or de-assign the box from the user.
    """
    if lab == "free":
        print("Free users cannot terminate machines. Please use reset instead.")
        sys.exit(1)
    print(f"Attempting to terminate {args.box.capitalize()}. This request often takes ~30 seconds, so be patient please...")
    res, message = api.terminate_machine(get_id(args.box))
    sys.exit(res)

def do_reset(args):
    """
    Handle the reset command.
    This will attempt to reset the specified box.
    NOTE: This command can take up to a couple minutes to 
    successfully reset and can be cancelled by other users.
    """
    print(f"Attempting to reset {args.box.capitalize()}. This request often takes ~30 seconds, so be patient please...")
    response = api.reset_machine(get_id(args.box))
    print(format_value(response))

def show_help(parser, command=None):
    args = []
    if command is not None:
        args = [command]
    if not "-h" in sys.argv and not "--help" in sys.argv:
        args.append('-h')
        print("\n")
        parser.parse_args(args)    

def parse_args():
    """
    Setup the argument parser. 
    The parser is setup to use subcommands so that each command can be extended in the future with its own arguments.
    """
    ArgumentParser()
    parser = ArgumentParser(
        prog="htb",
        description="This is a simple command line utility for interacting with the Hack the Box API. In order to use this tool you must find your api key in your HTB settings and configure this tool to use it with `htb config --apiKey=YOURAPIKEY`",
        epilog="You must set your apiKey by running: htb config --apiKey=APIKEY --lab=[free or vip]" if not apiKey else "Try: htb [command] --help"
    )
    command_parsers = parser.add_subparsers(title="commands", prog="htb")

    config_parser = command_parsers.add_parser("config", help="configure this tool")
    config_parser.add_argument("--apiKey", type=str, required=True, help="Your HTB api key. You can find this on your HTB settings page. THIS MUST BE SET BEFORE YOU CAN USE THIS TOOL FOR ANYTHING ELSE.")
    config_parser.add_argument("--lab", type=str, choices=["free", "vip"], required=True, help="Which lab you connect to, either free or vip. If you do not pay for your HTB account then you need to pass free or this wont work.")
    config_parser.set_defaults(func=do_config, command="config")

    list_parser = command_parsers.add_parser("list", help="list machines")
    list_parser.add_argument("--retired", action="store_true", help="Include retired boxes in the output. [NOTE: Retired boxes are only available to VIP users and cannot be accessed by a free user.]")
    list_parser.add_argument("--incomplete", action="store_true", help="Only show incomplete boxes in the output.\nAn incomplete box is one where you haven't owned both user and root.")
    list_parser.add_argument("-s", "--separator", type=str, default=" ", help="The separator to use when outputting the fields when -q is set")
    list_parser.add_argument("-rs", "--row-separator", type=str, default="\n", help="The separator to use between rows when outputting the fields when -q is set")
    list_parser.add_argument("-q", "--quiet", action="store_true", help="Output only the field values without any formatting. Useful when parsing the output.")
    list_parser.add_argument("-f", "--fields", metavar="field", default=["id", "name", "os", "rating", "owned_user", "owned_root", "active"], nargs="+", type=str, help="Limit the output to only these fields. All fields shown when this is omitted.")
    list_parser.add_argument("-a", "--all-fields", action="store_true", help="Output every field on the machines.")
    list_parser.set_defaults(func=do_list, command="list")

    info_parser = command_parsers.add_parser("info", help="get info about a machine")
    info_parser.add_argument("box", metavar="BOX",  type=str, help="The name of the box you want info for.")
    info_parser.add_argument("-s", "--separator", type=str, default=" ", help="The separator to use when outputting the fields when -q is set")
    info_parser.add_argument("-q", "--quiet", action="store_true", help="Output only the field values without any formatting. Useful when parsing the output.")
    info_parser.add_argument("-f", "--fields", metavar="field", nargs="+", type=str, help="Limit the output to only these fields. All fields shown when this is omitted.")
    info_parser.add_argument("-a", "--all-fields", action="store_true", help="Output every field on the machine.")
    info_parser.set_defaults(func=do_info, command="info")

    spawn_parser = command_parsers.add_parser("spawn", help="[VIP Only] spawn a machine")
    spawn_parser.add_argument("box", metavar="BOX",  type=str, help="The name of the box to spawn. This will fail if you have another box currently spawned. Terminate any spawned boxes and wait until it actually shuts down before running this.")
    spawn_parser.set_defaults(func=do_spawn, command="spawn")

    own_parser = command_parsers.add_parser("own", help="submit a flag to own a box")
    own_parser.add_argument("box", metavar="BOX",  type=str, help="The name of the box you want to own.")
    own_parser.add_argument("-f", "--flag", type=str, required=True, help="The flag you want to submit to own the box. user/root is automatically determined by the server based on what flag you submit.")
    own_parser.add_argument("-d", "--difficulty", required=True, type=int, metavar="[1-10]", choices=range(1,11), help="The rating of how difficult you thought it was from 1-10.")
    own_parser.set_defaults(func=do_own, command="own")

    terminate_parser = command_parsers.add_parser("terminate", help="[VIP Only] terminate a box")
    terminate_parser.add_argument("box", metavar="BOX",  type=str, help="The name of the box to terminate. Termination may take up to a few minutes to take effect. Until then you will not be able to spawn any new boxes.")
    terminate_parser.set_defaults(func=do_terminate, command="terminate")

    reset_parser = command_parsers.add_parser("reset", help="[Free Only] reset a box")
    reset_parser.add_argument("box", metavar="BOX",  type=str, help="The name of the box to reset. Resetting may take a few minutes to take effect and may be cancelled by another user. ")
    reset_parser.set_defaults(func=do_reset, command="reset")

    try:
        args = parser.parse_args()
    except:
        subcommand=None
        if len(sys.argv) >= 2:
            subcommand = sys.argv[1]
            show_help(parser, subcommand)
        sys.exit(1)
    return args, parser


if __name__ == "__main__":
    load_config()
    args, parser = parse_args()
    if "commmand" not in args:
        parser.print_help()
        sys.exit(1)
    if args.command != "config" and (not apiKey or not lab):
        print("You must configure your apiKey before interacting with the HTB API.\n\nTry running 'htb config --apiKey=[your apiKey here]'")
        sys.exit(1)
    init_api(apiKey)
    load_machines()
    args.func(args)