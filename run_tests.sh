#!/bin/bash

# Define Python versions
python_versions=("3.8" "3.9" "3.10" "3.11")

python_versions=("3.9")

skip_tests=false
if ! $skip_tests; then

    # Loop over Python versions
    for version in "${python_versions[@]}"; do
        echo $version
        # Create virtual environment
        if ! source activate mlxp_env_$version &> /dev/null; then
    #        # Create Conda environment
            conda create -n mlxp_env_$version python=$version -y
            pip install pytest
            pip install torch
        fi
        #source mlxp_env_$version/bin/activate
        source activate mlxp_env_$version
        
        # Install MLXP

        pip install torch
        pip install -e .
        # Run tests
        cd tests
        python -m pytest
        cd .. 
    done               

fi



# Build the documentation

version="3.9"
cd docs
pip install sphinx furo autodocsumm
sphinx-build -b html . _build/html


