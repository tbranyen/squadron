from git import *
import os
import time
import main
from fileio.config import parse_config
from log import setup_log, log

def daemonize(squadron_dir, config_file, polltime, repo, node_name):
    """
    Runs squadron every polltime minutes.

    Keyword arguments:
        squadron_dir -- squadron directory
        config_file -- config file or None for defaults
        polltime -- minutes to sleep in between runs
        repo -- source code for the squadron_dir for updating
        node_name -- override for nodename
        loglevel -- how much to log
    """
    log.debug('entering daemon.daemonize %s',
            [squadron_dir, config_file, polltime, repo])
    parsed_config = parse_config(log, config_file)
    print "Daemon is using loglevel: " + str(log.getEffectiveLevel())
    if not polltime:
        polltime = float(parsed_config['polltime'])
    else:
        polltime = float(polltime)

    squadron_dir = main.get_squadron_dir(squadron_dir, parsed_config)

    if not os.path.exists(squadron_dir):
        log.info('Cloning %s into %s', repo, squadron_dir)
        repo = Repo.clone_from(repo, squadron_dir)
    else:
        repo = Repo(squadron_dir)
    while(True):
        #We set the working dir back here incase any action changed it
        git = repo.git
        log.debug("Doing git checkout")
        out = git.checkout('master')
        log.debug('Git checkout returned: %s', out)
        log.debug('Doing git pull --rebase')
        out = git.pull('--rebase')
        log.debug('Git pull returned: %s', out)

        ret = main.go(squadron_dir, node_name=node_name, config_file=config_file, dry_run=False)
        log.debug('main.go returned: %s', ret)
        if ret:
            #TODO: Squadron sends bug to status API or some other remote server?
            log.error('Squadron had an error')
        log.debug('daemon is sleeping: %s', polltime)
        time.sleep(polltime)
