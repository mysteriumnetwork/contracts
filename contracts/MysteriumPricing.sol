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
  // https://www.coingecko.com/en/price_charts/ethereum/chf
  // 120.34587901 is 1203458
  uint public chfRate;

  uint public chfScale = 10000;

  /* How many weis one token costs */
  uint public hardCapPrice = 12000;  // 1.2 * 10000 Expressed as CFH base points

  uint public softCapPrice = 10000;  // 1.0 * 10000 Expressed as CFH base points

  uint public softCapCHF = 6000000 * 10000; // Soft cap set in CHF

  //Address of the ICO contract:
  Crowdsale public crowdsale;

  function MysteriumPricing(uint initialChfRate) {
    chfRate = initialChfRate;
  }

  /// @dev Setting crowdsale for setConversionRate()
  /// @param _crowdsale The address of our ICO contract
  function setCrowdsale(Crowdsale _crowdsale) onlyOwner {

    if(!_crowdsale.isCrowdsale()) {
      throw;
    }

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

  /**
   * Allow to set soft cap.
   */
  function setSoftCapCHF(uint _softCapCHF) onlyOwner {
    softCapCHF = _softCapCHF;
  }

  /**
   * Get CHF/ETH pair as an integer.
   *
   * Used in distribution calculations.
   */
  function getEthChfPrice() public constant returns (uint) {
    return chfRate / chfScale;
  }

  /**
   * Currency conversion
   *
   * @param  chf CHF price * 100000
   * @return wei price
   */
  function convertToWei(uint chf) public constant returns(uint) {
    return chf.times(10**18) / chfRate;
  }

  /// @dev Function which tranforms CHF softcap to weis
  function getSoftCapInWeis() public returns (uint) {
    return convertToWei(softCapCHF);
  }

  /**
   * Calculate the current price for buy in amount.
   *
   * @param  {uint amount} How many tokens we get
   */
  function calculatePrice(uint value, uint weiRaised, uint tokensSold, address msgSender, uint decimals) public constant returns (uint) {

    uint multiplier = 10 ** decimals;
    if (weiRaised > getSoftCapInWeis()) {
      //Here SoftCap is not active yet
      return value.times(multiplier) / convertToWei(hardCapPrice);
    } else {
      return value.times(multiplier) / convertToWei(softCapPrice);
    }
  }

}
