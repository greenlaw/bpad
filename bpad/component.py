from abc import ABC, abstractmethod
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class Component(ABC):
    """
    An abstract system component.

    A system component encapsulates a set of related configuration (e.g.
    terraform modules, kubernetes yaml definitions) and software (e.g. Python
    code, Docker images). For example, a subsystem with distinct
    responsibilities, with zero or more of its own subcomponents. Components
    are somewhat loosely-coupled, but are linked to other components via
    terraform module declarations and through things like triggers (SNS) and
    object storage (s3 buckets) that might be touched by multiple subsystems.

    This is an abstract class which should not be instantiated directly, but
    inherited from.

    Inheriting classes must implement all abstract methods, even if they don't
    have any effect.

    Attributes:
        path: Path to the directory containing component configuration files,
            source code, etc.
    """

    def __init__(self, path):
        self.path = path

    @staticmethod
    def _check_tfoutputs(tf_outputs, required_keys):
        """
        Verify that the provided terraform output dict has all required keys.

        Keys are first converted to upper case before comparing.

        If verification fails, an Exception is raised.

        Args:
            tf_outputs (`dict`): A `dict` representing all terraform outputs
                from a deployment's root-level module. Dict structure matches
                the structure of `terraform output -json`.
            required_keys (`list`): A `list` of required terraform outputs.

        Raises:
            AttributeError: If required_keys is not empty and tf_outputs is
                None.
            KeyError: If tf_outputs is missing any of required_keys.
        """
        if not required_keys or len(required_keys) == 0:
            return

        tf_output_keys_upper = [x.upper() for x in tf_outputs.keys()]
        for required_key in required_keys:
            if required_key.upper() not in tf_output_keys_upper:
                raise KeyError(f"Specified tf_outputs [{tf_outputs}] is missing one or more required_keys [{required_keys}]")

    @staticmethod
    def _set_env_vars(keys_values):
        """
        Set environment variables using supplied `dict`.

        An environment variable of the same key (but converted to upper case)
        will be set for each key-value pair.

        Args:
            keys_values (`dict`): A `dict` containing all desired keys/values.
        """
        if keys_values:
            for key in keys_values:
                os.environ[key.upper()] = keys_values[key]

    @staticmethod
    def _set_env_vars_from_tfoutputs(tf_outputs):
        """
        Set environment variables from a terraform output-style `dict`.

        An environment variable of the same key (but converted to upper case)
        will be set for each terraform output. The value will be converted to
        a string, even if the terraform output type is different.

        Args:
            tf_outputs (`dict`): A `dict` representing all terraform outputs
                from a deployment's root-level module. Dict structure matches
                the structure of `terraform output -json`.
        """
        if tf_outputs:
            for tf_output_key in tf_outputs:
                os.environ[tf_output_key.upper()] = str(tf_outputs[tf_output_key]["value"])

    @staticmethod
    def _kubectl_apply(yaml_path, expand_env_vars=True):
        """
        Perform a kubectl apply operation using the specified yaml file.

        Args:
            yaml_path (`str`): Path to yaml file on disk containing k8s
                configuration to be applied.
            expand_env_vars (`bool`): If True, k8s configuration will have any
                environment variabls (e.g. $VARNAME or ${VARNAME}) replaced
                with their present values, if any.

        Returns:
            The `CompletedProcess` object.

        Raises:
            CalledProcessError: If the kubectl command returned nonzero status.
            OSError: If there was a problem opening the yaml file.
        """
        cmd = "kubectl apply -f -"

        with open(yaml_path, 'r') as f:
            if expand_env_vars:
                k8s_yaml = os.path.expandvars(f.read())
            else:
                k8s_yaml = f.read()
            try:
                logger.info(f"Applying k8s yaml:\n{k8s_yaml}")
                return subprocess.run(
                    cmd.split(),
                    input=k8s_yaml,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"CalledProcessError encountered while attempting to apply yaml file [{yaml_path}].\nException: {e}\nSTDOUT: {e.output}\nSTDERR: {e.stderr}")
                raise e

    @staticmethod
    def _kubectl_apply_remote(yaml_url):
        """
        Perform a kubectl apply of remote yaml file

        Assumes there are no env vars to replace

        This functions probly goin in the trash

        Args:
            yaml_url (`str`): Path to yaml file on disk containing k8s
                configuration to be applied.

        Returns:
            The `CompletedProcess` object.

        Raises:
            CalledProcessError: If the kubectl command returned nonzero status.
            OSError: If there was a problem opening the yaml file.
        """
        cmd = f"kubectl apply -f {yaml_url}"

        try:
            logger.info(f"Applying k8s yaml from:\n{yaml_url}")
            return subprocess.run(
                cmd.split(),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"CalledProcessError encountered while attempting to apply yaml file [{yaml_url}].\nException: {e}\nSTDOUT: {e.output}\nSTDERR: {e.stderr}")
            raise e

    @staticmethod
    def _kubectl_create(yaml_path, expand_env_vars=True):
        """
        Perform a kubectl create operation using the specified yaml file.

        A create operation is needed (instead of apply) sometimes, e.g. when
        creating a job using `generateName` (i.e. asking k8s to assign a unique
        name to the created job pod).

        Args:
            yaml_path (`str`): Path to yaml file on disk containing k8s
                configuration to be created.
            expand_env_vars (`bool`): If True, k8s configuration will have any
                environment variabls (e.g. $VARNAME or ${VARNAME}) replaced
                with their present values, if any.

        Returns:
            The `CompletedProcess` object.

        Raises:
            CalledProcessError: If the kubectl command returned nonzero status.
            OSError: If there was a problem opening the yaml file.
        """
        cmd = "kubectl create -f -"

        with open(yaml_path, 'r') as f:
            if expand_env_vars:
                k8s_yaml = os.path.expandvars(f.read())
            else:
                k8s_yaml = f.read()
            try:
                logger.info(f"Creating resources using k8s yaml:\n{k8s_yaml}")
                return subprocess.run(
                    cmd.split(),
                    input=k8s_yaml,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"CalledProcessError encountered while attempting to create resources with yaml file [{yaml_path}].\nException: {e}\nSTDOUT: {e.output}\nSTDERR: {e.stderr}")
                raise e

    def build(self, deployment_name, nocache=False):
        pass

    def deploy(self, deployment_name, tf_outputs=None):
        pass

    def package(self, deployment_name):
        pass

    def undeploy(self, deployment_name, tf_outputs=None):
        pass

