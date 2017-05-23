

## Mysterium token and crowdsale features

* Zeppelin StandardToken with upgradeable trait (Golem like) and releaseable (owner can decide when tokens are transferred)

* Tokens are minted during the crowdsale (MysteriumCrowdsale.assignTokens)

* Extra tokens for founders, seed round, etc. are minted after the crowdsale is over (MysteriumTokenDistribution.distribute)

* Crowdsale priced in CHF (MysteriumPricing.setConversionRate)

* Pricing has soft and hard cap (MysteriumPricing.calculatePrice)

* Reaching soft cap triggers 72 hours closing time (MysteriumCrowdsale.triggerSoftCap)

* Crowdsale can whitelist early participants (Crowdsale.setEarlyParicipantWhitelist)

* Tokens are deposited to time locked vaults (MultiVault)

* Team funds are transferred through a 30 days delay vault (IntermediateVault)

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


                                                                           
