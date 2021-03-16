FROM jupyter/minimal-notebook@sha256:fcc16378ef8778c8c02491bfa0e952c3b9571e2f1600ea25bd3197349eda284c
# Singularity doesn't support users, but during build we need to be root.
# Always set back to 'jovyan' at the end.
USER root
# Install third-party dependencies
# ARG DEBIAN_FRONTEND=noninteractive
# RUN apt-get update && apt-get install -yq --no-install-recommends \
#     name \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*
# Install first-party dependencies
# TODO: pin a commit
RUN pip install -e git+https://github.com/xwcl/irods_fsspec.git@main#egg=irods-fsspec
# Install client
ADD . ./exao_dap_client/
RUN pip install -e ./exao_dap_client/
USER jovyan
