#!/bin/bash

# Define Python versions
python_versions=("3.8" "3.9" "3.10" "3.11")

#python_versions=("3.8")

# Loop over Python versions
for version in "${python_versions[@]}"; do
    echo $version
    # Create virtual environment
#    if ! conda activate mlxp_env_$version &> /dev/null; then
#        # Create Conda environment
#        conda create -n mlxp_env_$version python=$version -y
#    fi
    #source mlxp_env_$version/bin/activate
    source activate mlxp_env_$version
    
    # Install MLXP

    pip install pytest
    pip install -e .
    # Run tests
    cd tests
    python -m pytest
    cd .. 
done               
