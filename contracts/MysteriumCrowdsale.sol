pragma solidity ^0.4.7;

import "./Crowdsale.sol";
import "./MysteriumPricing.sol";
import "./MintableToken.sol";


contract MysteriumCrowdsale is Crowdsale {
  using SafeMathLib for uint;

  // Are we on the "end slope" (triggered after soft cap)
  bool softCapTriggered;

  function MysteriumCrowdsale(address _token, PricingStrategy _pricingStrategy, address _multisigWallet, uint _start, uint _end)
    Crowdsale(_token, _pricingStrategy, _multisigWallet, _start, _end, 0) {
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

  /**
   * Get minimum funding goal in wei.
   */
  function getMinimumFundingGoal() public constant returns (uint goalInWei) {
    return MysteriumPricing(pricingStrategy).convertToWei(700000 * 10000);
  }

  /**
   * @return true if the crowdsale has raised enough money to be a succes
   */
  function isMinimumGoalReached() public constant returns (bool reached) {
    return weiRaised >= getMinimumFundingGoal();
  }

  /**
   * Called from invest() to confirm if the curret investment does not break our cap rule.
   */
  function isBreakingCap(uint weiAmount, uint tokenAmount, uint weiRaisedTotal, uint tokensSoldTotal) constant returns (bool limitBroken) {
    return weiRaisedTotal > MysteriumPricing(pricingStrategy).convertToWei(10000000 * 10000);
  }

  function isCrowdsaleFull() public constant returns (bool) {
    return weiRaised >= MysteriumPricing(pricingStrategy).convertToWei(10000000 * 10000);
  }

  /**
   * Dynamically create tokens and assign them to the investor.
   */
  function assignTokens(address receiver, uint tokenAmount) private {
    MintableToken mintableToken = MintableToken(token);
    mintableToken.mint(receiver, tokenAmount);
  }

}
