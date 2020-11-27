import importlib
import json
import logging
import os

import yaml

from bpad.util import exec_cmd

"""
Default wait time (secs) after `terraform apply` before component deployment.
"""
APPLY_WAIT_DEFAULT = 60

logger = logging.getLogger(__name__)


class ComponentDefinition(yaml.YAMLObject):
    """
    A YAML-based mapping between a component directory and python class.

    This is used to allow a Deployment's components to be described in the
    `deployments.yml` file as simply a fully-qualified class name (e.g.
    `package.module.ClassName`) along with a path to the directory containing
    the component's terraform configuration, source code, or other related
    files.
    """

    yaml_tag = "!Component"

    def __init__(self, class_name, path):
        self.class_name = class_name
        self.path = path

    def __repr__(self):
        return f"Component(class_name: {self.class_name}, path: {self.path})"

    def get_instance(self):
        module_name, class_name = self.class_name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        class_ref = getattr(module, class_name)
        return class_ref(self.path)


class Deployment(yaml.YAMLObject):
    """
    A deployment.

    Attributes:
        name: Deployment name.
        path: Path to the deployment configuration directory.
        components: List of components attached to the deployment.
        apply_wait: Wait time (seconds) after infrastructure has been deployed
            with `terraform apply`, before component software is deployed.
        tf_outputs: Dict of the deployment's terraform outputs. Lazy-loaded
            upon access, since a Deployment object may be instantiated before
            the deployment itself has been through terraform init/apply. If
            None, it means terraform outputs are not available for this reason
            (or if an error was encountered trying to query them).
    """

    yaml_tag = "!Deployment"

    def __init__(self, name, path, components, apply_wait=APPLY_WAIT_DEFAULT):
        """
        Initializes a deployment.

        The `components` will be built/packaged/deployed in the order specified to this
        constructor.
        """
        self.name = name
        self.path = path
        self.components = components
        self.apply_wait = apply_wait
        self._tf_outputs = None

    def __repr__(self):
        return f"Deployment(name: {self.name}, path: {self.path}, components: {self.components})"

    @property
    def tf_outputs(self):
        """
        Dict of the deployment's terraform outputs, if available.

        Dict structure matches the JSON format of `terraform output -json`.

        The `terraform output` command is run every time this property is
        accessed to ensure the latest available values are provided.
        """
        try:
            prev_cwd = os.getcwd()
            os.chdir(self.path)
            proc = exec_cmd(f"terraform output -json", True, logger)
            self._tf_outputs = json.loads(proc.stdout.strip())
            return self._tf_outputs
        except Exception as e:
            logger.error(f"Error encountered attempting to read terraform outputs from deployment [{self.name}] at path [{self.path}]: \n\t{e.message}")
            raise e
        finally:
            os.chdir(prev_cwd)

    @tf_outputs.setter
    def tf_outputs(self, value):
        self._tf_outputs = value

    def apply(self):
        """
        Apply terraform-managed infrastructure, artifacts, and configuration.
        """
        try:
            prev_cwd = os.getcwd()
            os.chdir(self.path)
            proc = exec_cmd(f"terraform apply", True, logger)  # TODO: Add -auto-approve ?
            logger.info(proc.stdout.strip())
        except Exception as e:
            logger.error(f"Error encountered attempting to apply terraform config for deployment [{self.name}] at path [{self.path}]: \n\t{e.message}")
            raise e
        finally:
            os.chdir(prev_cwd)

    def bootstrap(self):
        raise NotImplementedError

    def build(self, nocache=False):
        """
        Perform a full build for the deployment.

        Args:
            nocache (`bool`): If True, force rebuild of cached artifacts (e.g.
                model index files). Default is False, meaning build steps for
                certain resources may be skipped if they already exist on disk.
        """
        for component in self.components:
            component.build(self.name, nocache)

    def deploy(self):
        """
        Deploy system component software.
        """
        logger.info("Deploying system components")
        for component in self.components:
            component.deploy(self.name, self.tf_outputs)

    def destroy(self):
        """
        Destroy terraform-managed infrastructure, artifacts, and configuration.
        """
        try:
            prev_cwd = os.getcwd()
            os.chdir(self.path)
            proc = exec_cmd(f"terraform destroy", True, logger)  # TODO: Add -auto-approve ?
            logger.info(proc.stdout.strip())
        except Exception as e:
            logger.error(f"Error encountered attempting to destroy terraform config for deployment [{self.name}] at path [{self.path}]: \n\t{e.message}")
            raise e
        finally:
            os.chdir(prev_cwd)

    def package(self):
        for component in self.components:
            component.package(self.name)

    def unbootstrap(self):
        # TODO: Call destroy first to make sure app infrastructure is torn down
        # before tearing down bootstrap infrastructure (otherwise the terraform
        # state would be lost and app infrastructure would need to be deleted
        # manually)
        raise NotImplementedError

    def undeploy(self):
        """
        Undeploy system component software.
        """
        logger.info("Un-deploying system components")
        for component in self.components:
            component.undeploy(self.name, self.tf_outputs)
