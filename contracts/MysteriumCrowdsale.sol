pragma solidity ^0.4.7;

import "./MintedTokenCappedCrowdsale.sol";

contract MysteriumCrowdsale is MintedTokenCappedCrowdsale {

  function MysteriumCrowdsale(address _token, PricingStrategy _pricingStrategy, address _multisigWallet, uint _start, uint _end, uint _minimumFundingGoal, uint _maximumSellableTokens)
    MintedTokenCappedCrowdsale(_token, _pricingStrategy, _multisigWallet, _start, _end, _minimumFundingGoal, _maximumSellableTokens) {}


}
