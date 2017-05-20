pragma solidity ^0.4.6;

import "./PricingStrategy.sol";
import "./SafeMathLib.sol";
import "./Crowdsale.sol";
import "zeppelin/contracts/ownership/Ownable.sol";

/**
 * Fixed crowdsale pricing - everybody gets the same price.
 */
contract MysteriumPricing is PricingStrategy, Ownable {

  using SafeMathLib for uint;

  // The conversion rate: how many weis is 1 CHF
  uint public chfRate;

  /* How many weis one token costs */
  uint public tokenPricePrimary;
  uint public tokenPriceSecondary;

  // Soft cap implementation in CHF
  uint public softCap;

  //Address of the ICO contract:
  Crowdsale crowdsale;

  function MysteriumPricing(uint _tokenPricePrimary, uint _tokenPriceSecondary, uint initialChfRate) {
    tokenPricePrimary = _tokenPricePrimary;
    tokenPriceSecondary = _tokenPriceSecondary;
    chfRate = initialChfRate;
  }

  /// @dev Setting crowdsale for setConversionRate()
  /// @param _crowdsale The address of our ICO contract
  function setCrowdsale(Crowdsale _crowdsale) onlyOwner {
    crowdsale = _crowdsale;
  }

  /// @dev Here you can set the new CHF/ETH rate
  /// @param _chfRate The rate how many weis is one CHF
  function setConversionRate(uint _chfRate) onlyOwner {
    //Here check if ICO is active
    if(now > crowdsale.startsAt())
      throw;

    chfRate = _chfRate;
  }


  /// @dev Function which tranforms CHF softcap to weis
  function getSoftCapInWeis() returns (uint) {
    return chfRate * softCap;
  }

  /// @dev Here you can set the softcap in CHF
  /// @param _softCap soft cap in CHF
  function setSoftCap(uint _softCap) onlyOwner {
    softCap = _softCap;
  }

  /**
   * Calculate the current price for buy in amount.
   *
   * @param  {uint amount} Buy-in value in wei.
   */
  function calculatePrice(uint value, uint tokensSold, uint weiRaised, address msgSender, uint decimals) public constant returns (uint) {
    uint multiplier = 10 ** decimals;
    
    if (getSoftCapInWeis() > weiRaised) {
      //Here SoftCap is not active yet
      return value.times(multiplier) / tokenPricePrimary;
    } else {
      return value.times(multiplier) / tokenPriceSecondary;
    }
  }

}
