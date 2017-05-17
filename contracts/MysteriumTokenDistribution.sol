pragma solidity ^0.4.6;

import "./Crowdsale.sol";
import "./CrowdsaleToken.sol";
import "./SafeMathLib.sol";

/**
 * At the end of the successful crowdsale allocate % bonus of tokens and other parties.
 *
 * Unlock tokens.
 *
 */
contract MysteriumTokenDistribution is FinalizeAgent {

  using SafeMathLib for uint;

  CrowdsaleToken public token;
  Crowdsale public crowdsale;

  /** Where we move the tokens at the end of the sale. */
  address public teamMultisig;

  uint public allocatedBonus;
  uint public bonusBasePoints;


  function MysteriumTokenDistribution(CrowdsaleToken _token, Crowdsale _crowdsale, address _teamMultisig, uint _bonusBasePoints) {
    token = _token;
    crowdsale = _crowdsale;
    if(address(crowdsale) == 0) {
      throw;
    }

    teamMultisig = _teamMultisig;
    if(address(teamMultisig) == 0) {
      throw;
    }

    bonusBasePoints = _bonusBasePoints;
  }

  /* Can we run finalize properly */
  function isSane() public constant returns (bool) {
    return (token.mintAgents(address(this)) == true) && (token.releaseAgent() == address(this));
  }

  /** Called once by crowdsale finalize() if the sale was success. */
  function finalizeCrowdsale() {
    if(msg.sender != address(crowdsale)) {
      throw;
    }

    // How many % of tokens the founders and others get
    uint tokensSold = crowdsale.tokensSold();
    allocatedBonus = tokensSold.times(bonusBasePoints) / 10000;

    // move tokens to the team multisig wallet
    token.mint(teamMultisig, 000);

    // Make token transferable
    token.releaseTokenTransfer();
  }

}
