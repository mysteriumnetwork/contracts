pragma solidity ^0.4.7;

import "./MintedEthCappedCrowdsale.sol";
import "./MysteriumPricing.sol";

contract MysteriumCrowdsale is MintedEthCappedCrowdsale {
  using SafeMathLib for uint;

  // Are we on the "end slope" (triggered after soft cap)
  bool softCapTriggered;

  function MysteriumCrowdsale(address _token, PricingStrategy _pricingStrategy, address _multisigWallet, uint _start, uint _end, uint _minimumFundingGoal, uint chfCap)
    MintedEthCappedCrowdsale(_token, _pricingStrategy, _multisigWallet, _start, _end, _minimumFundingGoal, chfCap) {
    weiCap = chfCap * MysteriumPricing(pricingStrategy).chfRate();
  }

  /// @dev triggerSoftCap triggers the earlier closing time
  function triggerSoftCap() {
    if(softCapTriggered)
      throw;

    uint softCap = MysteriumPricing(pricingStrategy).getSoftCapInWeis();

    if(softCap > weiRaised)
      throw;

    // When contracts are updated from upstream, you should use:
    // setEndsAt (now + 24 hours);
    endsAt = now + 24 hours;

    softCapTriggered = true;
  }
}
