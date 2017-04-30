

## Installation

OSX or Linux required.

[Install solc 0.4.8](http://solidity.readthedocs.io/en/develop/installing-solidity.html#binary-packages). This exact version is required. Read full paragraph how to install it on OSX.

Install Populus in Python virtual environment.

Clone the repository and initialize submodules:

    git clone --recursive git@github.com:MysteriumNetwork/contracts.git

First Install Python 3.5. Then in the repo folder:

    cd contracts
    python3.5 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install -e ico
    
Then test solc:

    solc --version
    
    solc, the solidity compiler commandline interface
    Version: 0.4.8+commit.60cc1668.Darwin.appleclang
    
Then test populus:
                                         
    populus          
    
    Usage: populus [OPTIONS] COMMAND [ARGS]...
    ...
                                                
## Compiling contracts
                   
Compile:                   
                             
    populus compile                                
                              
Output will be in `build` folder.                                       
                                        
## Running tests

Tests are written using `py.test` in tests folder.


                                                                           
