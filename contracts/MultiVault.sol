pragma solidity ^0.4.8;

import "zeppelin/contracts/token/StandardToken.sol";

/**
 *
 * Time-locked token vault of allocated tokens for founders.
 *
 * First used by Lunyr https://github.com/Lunyr/crowdsale-contracts
 */
contract MultiVault is SafeMath {

  /** Interface flag to determine if address is for a real contract or not */
  bool public isTimeVault = true;

  /** Token we are holding */
  StandardToken public token;

  /** Address that can claim tokens */
  address[] addresses;
  uint fullAmount; // What is 100%, this defines the scale, like 10000.
  uint[] percents; // These defines how many percents ((fullAmount/100)*percents)

  /** UNIX timestamp when tokens can be claimed. */
  uint256 public unlockedAt;

  event Unlocked();

  /// @dev You specify here who are the owners and which are their percents.
  ///      You can also specify what is 100% (fullAmount), so this is flexible.
  function MultiVault(StandardToken _token, uint _unlockedAt, address[] _addresses, uint[] _percents, uint _fullAmount) {
    if (_addresses.length != _percents.length)
      throw;

    token = _token;
    unlockedAt = _unlockedAt;

    addresses = _addresses;
    percents = _percents;
    fullAmount = _fullAmount;

    // Sanity check
    if (address(token) == 0x0) throw;
  }

  function getTokenBalance() public constant returns (uint) {
    return token.balanceOf(address(this));
  }

  /// @notice Transfer locked tokens to Lunyr's multisig wallet
  function unlock() public {
    // Wait your turn!
    if (now < unlockedAt) throw;

    uint tokenBalance = getTokenBalance();

    // StandardToken will throw in the case of transaction fails
    for (uint i=0; i <= (addresses.length-1); i++)
        token.transfer(addresses[i], tokenBalance/(fullAmount/percents[i]));

    Unlocked();
  }

  // disallow ETH payment for this vault
  function () { throw; }

}
