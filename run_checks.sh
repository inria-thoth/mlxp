#!/bin/bash





# Linting

#isort mlxp
#docformatter --recursive --in-place --wrap-summaries 88 --wrap-descriptions 88 mlxp
#black mlxp --line-length=110

#flake8 mlxp --count --select=E9,F63,F7,F82 --show-source --statistics
#flake8 mlxp --count --max-complexity=10 --max-line-length=110 --statistics
find mlxp -type f -name "*.py" | xargs pylint


# Define Python versions
python_versions=("3.8" "3.9" "3.10" "3.11")

python_versions=("3.9")

skip_tests=true
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

skip_doc=true
if ! $skip_doc; then
    pip install sphinx furo autodocsumm sphinx_multiversion
    cd docs
    sphinx-multiversion . _build/html
fi


