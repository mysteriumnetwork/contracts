pragma solidity ^0.4.7;

import "./Crowdsale.sol";
import "./MysteriumPricing.sol";
import "./MintableToken.sol";


contract MysteriumCrowdsale is Crowdsale {
  using SafeMathLib for uint;

  // Are we on the "end slope" (triggered after soft cap)
  bool public softCapTriggered;

  // The default minimum funding limit 7,000,000 CHF
  uint public minimumFundingCHF = 700000 * 10000;

  uint public hardCapCHF = 14000000 * 10000;

  function MysteriumCrowdsale(address _token, PricingStrategy _pricingStrategy, address _multisigWallet, uint _start, uint _end)
    Crowdsale(_token, _pricingStrategy, _multisigWallet, _start, _end, 0) {
  }

  /// @dev triggerSoftCap triggers the earlier closing time
  function triggerSoftCap() private {
    if(softCapTriggered)
      throw;

    uint softCap = MysteriumPricing(pricingStrategy).getSoftCapInWeis();

    if(softCap > weiRaised)
      throw;

    // When contracts are updated from upstream, you should use:
    // setEndsAt (now + 24 hours);
    endsAt = now + (3*24*3600);
    EndsAtChanged(endsAt);

    softCapTriggered = true;
  }

  /**
   * Hook in to provide the soft cap time bomb.
   */
  function onInvest() internal {
     if(!softCapTriggered) {
         uint softCap = MysteriumPricing(pricingStrategy).getSoftCapInWeis();
         if(weiRaised > softCap) {
           triggerSoftCap();
         }
     }
  }

  /**
   * Get minimum funding goal in wei.
   */
  function getMinimumFundingGoal() public constant returns (uint goalInWei) {
    return MysteriumPricing(pricingStrategy).convertToWei(minimumFundingCHF);
  }

  /**
   * Allow reset the threshold.
   */
  function setMinimumFundingLimit(uint chf) onlyOwner {
    minimumFundingCHF = chf;
  }

  /**
   * @return true if the crowdsale has raised enough money to be a succes
   */
  function isMinimumGoalReached() public constant returns (bool reached) {
    return weiRaised >= getMinimumFundingGoal();
  }

  function getHardCap() public constant returns (uint capInWei) {
    return MysteriumPricing(pricingStrategy).convertToWei(hardCapCHF);
  }

  /**
   * Reset hard cap.
   *
   * Give price in CHF * 10000
   */
  function setHardCapCHF(uint _hardCapCHF) onlyOwner {
    hardCapCHF = _hardCapCHF;
  }

  /**
   * Called from invest() to confirm if the curret investment does not break our cap rule.
   */
  function isBreakingCap(uint weiAmount, uint tokenAmount, uint weiRaisedTotal, uint tokensSoldTotal) constant returns (bool limitBroken) {
    return weiRaisedTotal > getHardCap();
  }

  function isCrowdsaleFull() public constant returns (bool) {
    return weiRaised >= getHardCap();
  }

  /**
   * @return true we have reached our soft cap
   */
  function isSoftCapReached() public constant returns (bool reached) {
    return weiRaised >= MysteriumPricing(pricingStrategy).getSoftCapInWeis();
  }


  /**
   * Dynamically create tokens and assign them to the investor.
   */
  function assignTokens(address receiver, uint tokenAmount) private {
    MintableToken mintableToken = MintableToken(token);
    mintableToken.mint(receiver, tokenAmount);
  }

}
