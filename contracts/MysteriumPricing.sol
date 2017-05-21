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
  uint public tokenPricePrimary = 12000;  // Expressed as CFH base points

  uint public tokenPriceSecondary = 10000;  // Expressed as CFH base points

  // Soft cap implementation in CHF
  uint public softCap;

  //Address of the ICO contract:
  Crowdsale crowdsale;

  function MysteriumPricing(uint initialChfRate) {
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
    return convertToWei(6000000 * 10000);
  }

  /**
   * Calculate the current price for buy in amount.
   *
   * @param  {uint amount} Buy-in value in wei.
   */
  function calculatePrice(uint value, uint weiRaised, uint tokensSold, address msgSender, uint decimals) public constant returns (uint) {

    uint multiplier = 10 ** decimals;

    if (getSoftCapInWeis() > weiRaised) {
      //Here SoftCap is not active yet
      return value.times(multiplier) / convertToWei(tokenPricePrimary);
    } else {
      return value.times(multiplier) / convertToWei(tokenPriceSecondary);
    }
  }

}
