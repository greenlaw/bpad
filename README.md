# Build-Package-Apply-Deploy (bpad)

A simple Python package to support cloud app deployment lifecycle.

## Summary

Sort of like a dumb Make, but written in OO Python. Instead of a `Makefile`, you define a `deployments.yml` which describes one or more distinct Terraform-based application deployments.

Each deployment points to the directory containing its corresponding Terraform root module, and is associated with one or more app components.

Each component points to a directory containing a Terraform module alongside app source code, Dockerfiles, or other support files--anything related to that portion of your app--and is associated with a Python class defining any required build, packaging, deploy, or undeploy steps.

Each component may also have zero or more subcomponents, allowing complex app hierarchies to be defined.

The CLI class can also be inherited from / extended to implement arbitrary CLI operations.

The primary built-in operations are:

* Build
  * Run `docker build` or any other build operations required by your app.
* Package
  * Generate any required deployment artifacts. For example, packaging up libraries into a ZIP archive that will be uploaded to s3 by Terraform (e.g. for defining an AWS Lambda Layer).
* Apply
  * Run `terraform apply` on the target deployment to initialize cloud resources.
* Deploy
  * Run any post-Terraform deployment steps for your app. For example, deploy Kubernetes resources to an EKS cluster created during the Apply phase.
* Undeploy
  * Reverse some or all actions performed during the deploy step.


## Installation

To install in editable (development) mode:

```pip install -e .```

or to install normally:

```pip install .```

