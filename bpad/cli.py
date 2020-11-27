#!/usr/bin/env python3
"""
Build, deploy, and manage cloud app infrastructure and software.

Before running this tool, the ``BPAD_TARGET`` environment variable may be set
to the directory containing the ``deployments.yml`` file describing any
deployments you wish to manage. If not set, the current working directory is
used.
"""
import logging
import os

import fire
import yaml
from bpad.util import exec_cmd
import json

# Must import Deployment in order for YAML loader to work, but need to ignore
# flake8 unused import warning F401
from bpad.deployment import Deployment  # noqa: F401

"""
Default logging level.
"""
LOGGING_LEVEL = logging.DEBUG

# Use global/module-level logging
logging.basicConfig(level=LOGGING_LEVEL)
logger = logging.getLogger(__name__)

"""
Name of environment variable pointing to top-level project directory.
"""
ENV_BPAD_TARGET = "BPAD_TARGET"

"""
Path to top-level project directory
"""
BASE_DIR = ""
if ENV_BPAD_TARGET in os.environ:
    BASE_DIR = os.environ[ENV_BPAD_TARGET]

"""
Name/path of deployment configuration YAML file.
"""
DEPLOYMENTS_YML = "deployments.yml"


class CLI:
    """
    Container for methods exposed thru CLI via Python Fire.
    """

    def __init__(self):
        deployments = self._load_deployments()
        self.deployments = {}
        for dep in deployments:
            self.deployments[dep.name] = dep

    @staticmethod
    def _check_paths(deployment):
        """
        Confirm existence of expected directory structure or print error.
        """
        try:
            if not os.path.isdir(deployment.path):
                raise FileNotFoundError()
            for comp in deployment.components:
                if not os.path.isdir(comp.path):
                    raise FileNotFoundError()
        except FileNotFoundError:
            logger.error(f"The specified path for deployment [{deployment.name}], or one of its components, was not found. Please ensure that the paths specified in [{DEPLOYMENTS_YML}] are either 1) absolute paths, 2) relative to your current working directory, or 3) relative to the path stored in the {ENV_BPAD_TARGET} environment variable.")
            raise SystemExit(1)

        return True

    def _load_deployments(self):
        """
        Read deployments yaml config and return corresponding objects.
        """
        deployments = []
        with open(DEPLOYMENTS_YML, "rb") as dep_yaml:
            deployments = yaml.load(dep_yaml.read(), Loader=yaml.Loader)
            for dep in deployments:
                if len(BASE_DIR) > 0 and not BASE_DIR.endswith(os.sep):
                    dep.path = os.sep.join((BASE_DIR, dep.path))
                comps = []
                for comp in dep.components:
                    comps.append(comp.get_instance())
                dep.components = comps
        return deployments

    def apply(self, deployment_name):
        """
        Apply deployment configuration and stand up infrastructure w/terraform.

        Args:
            deployment_name (`str`): Name of target deployment.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].apply()

    def bootstrap(self, deployment_name):
        """
        Create/update a deployment's terraform backend and related resources.

        Args:
            deployment_name (`str`): Name of target deployment.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].bootstrap()

    def build(self, deployment_name, nocache=False):
        """
        Build dependencies and docker images.

        Args:
            deployment_name (`str`): Name of target deployment.
            nocache (`bool`): If True, force rebuild of cached artifacts (e.g.
                model index files). Default is False, meaning build steps for
                certain resources may be skipped if they already exist on disk.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].build(nocache)

    def deploy(self, deployment_name):
        """
        Deploy system component software to cloud infrastructure.

        Before deployment, apply should have been run. to create required cloud
        infrastructure.

        Args:
            deployment_name (`str`): Name of target deployment.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].deploy()

    def destroy(self, deployment_name):
        """
        Destroy existing cloud resources via terraform.

        Args:
            deployment_name (`str`): Name of target deployment.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].destroy()

    def package(self, deployment_name):
        """
        Prepare/package all artifacts for deployment.

        Args:
            deployment_name (`str`): Name of target deployment.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].package()

    def unbootstrap(self, deployment_name):
        """
        Destroy a deployment's terraform backend and related resources.

        Args:
            deployment_name (`str`): Name of target deployment.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].unbootstrap()

    def undeploy(self, deployment_name):
        """
        Undeploy system component software to cloud infrastructure.

        This should undo any changes made during the `deploy` step.

        Args:
            deployment_name (`str`): Name of target deployment.
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        self.deployments[deployment_name].undeploy()

    def aws_mfa_login(self, deployment_name, mfa_token):
        """
        Retrieve/set temporary credentials for AWS login using MFA

        Requires environment variable: MFA_DEVICE_ARN is set containing arn of
        MFA device for account
        ex. export MFA_DEVICE_ARN=arn:aws:iam::1234567890:mfa/Your.IAM.Name

        Requires your original AWS secret keys are stored in ~/.aws/credentials
        under profile of form: <deplpyment_name>-auth for the deployment you
        intend to log in with

        Args:
            deployment_name (`str`): Name of target deployment.
            mfa_token ('str'): code given from you MFA device
        """
        try:
            self._check_paths(self.deployments[deployment_name])
        except KeyError as e:
            logger.error(f"Invalid deployment specified: {deployment_name}\n    Supported values: " + (", ").join(self.deployments.keys()) + f"\n\tException: {e}")
            raise SystemExit(1)

        MFA_DEVICE_ARN = os.getenv('MFA_DEVICE_ARN')
        AWS_AUTH_PERSISTENT_PROFILE = f"{deployment_name}-auth"

        if not MFA_DEVICE_ARN:
            logger.error(
                f"Env var: MFA_DEVICE_ARN not set. (Must be set with arn of your mfa device for IAM profile you are logging in with)"
            )
            raise SystemExit(1)

        cmd = f"aws --profile {AWS_AUTH_PERSISTENT_PROFILE} sts get-session-token --serial-number {MFA_DEVICE_ARN} --token-code {mfa_token}"
        cmd_result = exec_cmd(cmd)

        session_credentials = json.loads(cmd_result.stdout)

        cmd = f"aws --profile {deployment_name} configure set aws_access_key_id {session_credentials['Credentials']['AccessKeyId']}"
        exec_cmd(cmd)
        cmd = f"aws --profile {deployment_name} configure set aws_secret_access_key {session_credentials['Credentials']['SecretAccessKey']}"
        exec_cmd(cmd)
        cmd = f"aws --profile {deployment_name} configure set aws_session_token {session_credentials['Credentials']['SessionToken']}"
        exec_cmd(cmd)


def main():
    fire.Fire(CLI())


if __name__ == "__main__":
    main()
