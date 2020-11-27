"""
Simple utility functions for building, packaging, and deploying software.
"""
import logging
import subprocess

logger = logging.getLogger(__name__)


def exec_cmd(cmd, check_return=True, shell_mode=False, input=None):
    """
    Execute an external command using ``subprocess``.

    The command being run and its output are both logged. Any commands
    returning non-zero status will raise an exception.

    Args:
        cmd (`str`): A command to execute (if it relies on the shell, also
            pass ``shell_mode=True``)
        check_return (`bool`): Optional arg, True to throw error on
            non-zero return codes, False to allow failure (error code can
            be retrieved from ``CompletedProcess.returncode``).
        shell_mode (`bool`): Optional arg, True to use shell to execute
            command.

    Returns:
        ``CompletedProcess`` Object.
    """
    cmd = cmd.strip()
    if not shell_mode:
        cmd = cmd.split()

    logger.info(f"Executing command: {cmd}")
    try:
        proc = subprocess.run(
            cmd,
            input=input,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=check_return,
            text=True,
            shell=shell_mode)
        logger.info("Command Result: {}".format(proc.stdout))

        return proc
    except subprocess.CalledProcessError as e:
        logger.error(f"CalledProcessError encountered while running command [{cmd}]{' with input: ' + input if input is not None else ''}.\nException: {e}\nSTDOUT: {e.output}\nSTDERR: {e.stderr}")
        raise e

