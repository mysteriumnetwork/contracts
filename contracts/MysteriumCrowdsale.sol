pragma solidity ^0.4.7;

import "./MintedTokenCappedCrowdsale.sol";

contract MysteriumCrowdsale is MintedTokenCappedCrowdsale {
  using SafeMathLib for uint;
  uint chfRate;
  // Are we on the "end slope" (triggered after soft cap)
  bool isEndSlope;
  // Soft cap implementation
  uint softCap;
  // Addresses
  address[] vaults;

  function MysteriumCrowdsale(address _token, PricingStrategy _pricingStrategy, address _multisigWallet, uint _start, uint _end, uint _minimumFundingGoal, uint _maximumSellableTokens, uint _chfRate)
    MintedTokenCappedCrowdsale(_token, _pricingStrategy, _multisigWallet, _start, _end, _minimumFundingGoal, _maximumSellableTokens) {
    //Setting the rate here
    setRate(_chfRate);
  }

  /// @dev Here you can set the softcap in weis
  /// @param _softCap soft cap in tokens
  function setSoftCap(uint _softCap) onlyOwner {
    softCap = _softCap;
  }

  /// @dev Here you can set the ny CHF/ETH rate
  /// @param _chfRate The rate how many weis is one CHF
  function setRate(uint _chfRate) onlyOwner {
    chfRate = _chfRate;
  }

  /// @dev Function which tranforms CHF softcap to weis

  /// @dev EndSlope means the period after hard cap
  function beginEndSlope() {
    if(isEndSlope)
      throw;

    if(softCap > weiRaised)
      throw;

    // When contracts are updated from upstream, you should use:
    // setEndsAt (now + 24 hours);
    endsAt = now + 24 hours;

    isEndSlope = true;
  }
}
