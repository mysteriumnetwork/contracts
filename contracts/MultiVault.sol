pragma solidity ^0.4.6;


import "./Crowdsale.sol";
import "./SafeMathLib.sol";
import "./StandardToken.sol";

/**
 * Collect funds from presale investors, buy tokens for them in a single transaction and distribute out tokens.
 *
 * - Collect funds from pre-sale investors
 * - Send funds to the crowdsale when it opens
 * - Allow owner to set the crowdsale
 * - Have refund after X days as a safety hatch if the crowdsale doesn't materilize
 * - Allow unlimited investors
 *
 */
contract MultiVault is Ownable {

  using SafeMathLib for uint;

  /** How many investors we have now */
  uint public investorCount;

  /** How many wei we have raised totla. */
  uint public weiRaisedTotal;

  /** Who are our investors (iterable) */
  address[] public investors;

  /** How much they have invested */
  mapping(address => uint) public balances;

  /** How many tokens investors have claimed */
  mapping(address => uint) public claimed;

  /** When our refund freeze is over (UNIT timestamp) */
  uint public freezeEndsAt;

  /** What is the minimum buy in */
  uint public weiMinimumLimit;

  /** How many tokens were bought */
  uint public tokensBought;

   /** How many investors have claimed their tokens */
  uint public claimCount;

  /** Our ICO contract where we will move the funds */
  Crowdsale public crowdsale;

  /** We can also define our own token, which will override the ICO one ***/
  FractionalERC20 public token;

  /** What is our current state. */
  enum State{Unknown, Holding, Distributing}

  /** Somebody loaded their investment money */
  event Invested(address investor, uint value);

  /** Refund claimed */
  event Refunded(address investor, uint value);

  /** We executed our buy */
  event TokensBoughts(uint count);

  /** We distributed tokens to an investor */
  event Distributed(address investors, uint count);

  /**
   * Create presale contract where lock up period is given days
   */
  function MultiVault(address _owner, uint _freezeEndsAt) {

    owner = _owner;

    // Give argument
    if(_freezeEndsAt == 0) {
      throw;
    }

    freezeEndsAt = _freezeEndsAt;
  }

  /**
   * Get the token we are distributing.
   */
  function getToken() public constant returns(FractionalERC20) {
    if (address(token) > 0)
      return token;

    if(address(crowdsale) == 0)  {
      throw;
    }

    return crowdsale.token();
  }

  /**
   * Participate to a presale.
   */
  function addInvestor(address investor, uint amount) public onlyOwner payable {

    // Cannot invest anymore through crowdsale when moving has begun
    if(getState() == State.Distributing) throw;

    bool existing = balances[investor] > 0;

    balances[investor] = balances[investor].plus(amount);

    // This is a new investor
    if(!existing) {
      investors.push(investor);
      investorCount++;
    }

    weiRaisedTotal = weiRaisedTotal.plus(amount);

    Invested(investor, amount);
  }

  /**
   * How may tokens each investor gets.
   */
  function getClaimAmount(address investor) public constant returns (uint) {
    if(getState() != State.Distributing) {
      throw;
    }
    return balances[investor].times(getToken().balanceOf(address(this))) / weiRaisedTotal;
  }

  /**
   * How many tokens remain unclaimed for an investor.
   */
  function getClaimLeft(address investor) public constant returns (uint) {
    getClaimAmount(investor).minus(claimed[investor]);
  }

  /**
   * Claim all remaining tokens for this investor.
   */
  function claimAll() {
    claim(getClaimLeft(msg.sender));
  }

  /**
   * Claim N bought tokens to the investor as the msg sender.
   *
   */
  function claim(uint amount) {
    address investor = msg.sender;

    if(getClaimLeft(investor) < amount) {
      // Woops we cannot get more than we have left
      throw;
    }

    claimed[investor] = claimed[investor].plus(amount);
    getToken().transfer(investor, amount);

    Distributed(investor, amount);
  }

  /**
   * Set the target crowdsale where we will move presale funds when the crowdsale opens.
   */
  function setCrowdsale(Crowdsale _crowdsale) public onlyOwner {
    crowdsale = _crowdsale;
  }

  /**
   * Set the target token, which overrides the ICO token.
   */
  function setToken(FractionalERC20 _token) public onlyOwner {
    token = _token;
  }

  /**
   * Resolve the contract umambigious state.
   */
  function getState() public returns(State) {
    if(getToken().balanceOf(address(this)) == 0) {
      return State.Unknown;
    } else if(now < freezeEndsAt) {
      return State.Holding;
    } else {
      return State.Distributing;
    }
  }

  /** Explicitly call function from your wallet. */
  function() payable {
    throw;
  }
}
