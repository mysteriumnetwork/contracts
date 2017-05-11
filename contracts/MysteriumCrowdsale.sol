pragma solidity ^0.4.7;

import "./Crowdsale.sol";

contract MysteriumCrowdsale is Crowdsale {

  function MysteriumCrowdsale(address _token, PricingStrategy _pricingStrategy, address _multisigWallet, uint _start, uint _end, uint _minimumFundingGoal)
    Crowdsale(_token, _pricingStrategy, _multisigWallet, _start, _end, _minimumFundingGoal) {}


}
