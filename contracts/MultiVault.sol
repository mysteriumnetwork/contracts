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

  /** How many wei we have raised total. We use this as the distribution total amount. However because investors are added by hand this can be direct percentages too. */
  uint public weiRaisedTotal;

  /** Who are our investors (iterable) */
  address[] public investors;

  /** How much they have invested */
  mapping(address => uint) public balances;

  /** How many tokens investors have claimed */
  mapping(address => uint) public claimed;

  /** When our claim freeze is over (UNIT timestamp) */
  uint public freezeEndsAt;

  /** Our ICO contract where we will move the funds */
  Crowdsale public crowdsale;

  /** We can also define our own token, which will override the ICO one ***/
  FractionalERC20 public token;

  /** How many tokens were deposited on the vautl */
  uint public initialTokenBalance;

  /* Has owner set the initial balance */
  bool public initialTokenBalanceFetched;

  /** What is our current state. */
  enum State{Unknown, Holding, Distributing}

  /** Somebody loaded their investment money */
  event Invested(address investor, uint value);

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
  function addInvestor(address investor, uint amount) public onlyOwner {

    // Cannot invest anymore through crowdsale when moving has begun
    if(getState() != State.Holding) throw;

    if(amount == 0) throw; // No empty buys

    bool existing = balances[investor] > 0;

    if(existing) {
      // Guarantee data load against race conditiosn
      // and fat fingers, so that we can load one investor only once
      throw;
    }

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

    if(!initialTokenBalanceFetched) {
      throw;
    }

    return initialTokenBalance.times(balances[investor]) / weiRaisedTotal;
  }

  /**
   * How many tokens remain unclaimed for an investor.
   */
  function getClaimLeft(address investor) public constant returns (uint) {
    return getClaimAmount(investor).minus(claimed[investor]);
  }

  /**
   * Claim all remaining tokens for this investor.
   */
  function claimAll() {
    claim(getClaimLeft(msg.sender));
  }

  /**
   * Only owner is allowed to set the vault initial token balance.
   *
   * Because only owner can guarantee that the all tokens have been moved
   * to the vault and it can begin disribution. Otherwise somecone can
   * call this too early and lock the balance to zero or some other bad value.
   */
  function fetchTokenBalance() onlyOwner {
    // Caching fetched token amount:
    if (!initialTokenBalanceFetched) {
        initialTokenBalance = getToken().balanceOf(address(this));
        if(initialTokenBalance == 0) throw; // Somehow in invalid state
        initialTokenBalanceFetched = true;
    } else {
      throw;
    }
  }

  /**
   * Claim N bought tokens to the investor as the msg sender.
   *
   */
  function claim(uint amount) {
    address investor = msg.sender;

    if(!initialTokenBalanceFetched) {
      // We need to have the balance before we start
      throw;
    }

    if(getState() != State.Distributing) {
      // We are not distributing yet
      throw;
    }

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
    if(now > freezeEndsAt && initialTokenBalanceFetched) {
      return State.Distributing;
    } else {
      return State.Holding;
    }
  }

  /** Explicitly call function from your wallet. */
  function() payable {
    throw;
  }
}
