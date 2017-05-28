pragma solidity ^0.4.6;

import "./Crowdsale.sol";
import "./CrowdsaleToken.sol";
import "./SafeMathLib.sol";
import "./MysteriumPricing.sol";
import "zeppelin/contracts/ownership/Ownable.sol";

/**
 * At the end of the successful crowdsale allocate % bonus of tokens and other parties.
 *
 * Unlock tokens.
 *
 */
contract MysteriumTokenDistribution is FinalizeAgent, Ownable {

  using SafeMathLib for uint;

  CrowdsaleToken public token;
  Crowdsale public crowdsale;

  /** Where we move the tokens at the end of the sale. */
  address public teamMultisig;

  MysteriumPricing mysteriumPricing;

  // Vaults:
  address futureRoundVault;
  address foundationWallet;
  address teamVault;
  address seedVault1; //  0
  address seedVault2; //  12 months

  // Constants for distribute()
  uint SOFT_CAP_CHF = 6000000;
  uint MIN_SOFT_CAP_CHF = 2000000;
  uint SEED_RAISED_ETH = 6000;
  uint FOUNDATION_PERCENTAGE = 9;
  uint TEAM_PERCENTAGE = 10;
  //uint public EARLYBIRD_PRICE_MULTIPLIER = 1.2;
  uint REGULAR_PRICE_MULTIPLIER = 1;
  uint multiplier = 10 ** 8;

  // Expose the state of distribute for the examination
  uint public earlybird_coins;
  uint public regular_coins;
  uint public seed_coins;
  uint public total_coins;
  uint public future_round_coins;
  uint public foundation_coins;
  uint public team_coins;
  uint public seed_coins_vault1;
  uint public seed_coins_vault2;
  uint public seed_multiplier;
  uint public future_round_percentage;
  uint public percentage_of_three;
  uint public earlybird_percentage;

  function MysteriumTokenDistribution(CrowdsaleToken _token, Crowdsale _crowdsale, MysteriumPricing _mysteriumPricing) {
    token = _token;
    crowdsale = _crowdsale;
    if(address(crowdsale) == 0) {
      throw;
    }

    mysteriumPricing = _mysteriumPricing;
  }

  function distribute(uint amount_raised_chf, uint eth_chf_price) {
    // Distribute:
    // seed coins
    // foundation coins
    // team coins

    if(msg.sender == address(crowdsale) || msg.sender == owner) {
      // Only crowdsal contract or owner (manually) can trigger the distribution
      throw;
    }

    // step 1
    if (amount_raised_chf <= SOFT_CAP_CHF) {
       earlybird_coins = amount_raised_chf.times(multiplier).plus(amount_raised_chf.times(multiplier)/5);
    }
    else {
      earlybird_coins = SOFT_CAP_CHF.times(multiplier).plus(SOFT_CAP_CHF.times(multiplier)/5);
    }

    // step 2
    regular_coins = 0;
    if (amount_raised_chf > SOFT_CAP_CHF) {
      regular_coins = (amount_raised_chf.minus(SOFT_CAP_CHF)).times(multiplier).times(REGULAR_PRICE_MULTIPLIER);
    }

    // step 3
    // 2M - 1x
    // 6M - 5x
    if (amount_raised_chf <= MIN_SOFT_CAP_CHF) {
        seed_multiplier = multiplier.times(1);
    } else if (amount_raised_chf > MIN_SOFT_CAP_CHF && amount_raised_chf < SOFT_CAP_CHF) {
        seed_multiplier = ((amount_raised_chf / 1000000).minus(1)).times(multiplier);

    } else /*if (amount_raised_chf >= SOFT_CAP_CHF)*/ {
        seed_multiplier = multiplier.times(5);
    }

    // step 4
    seed_coins = SEED_RAISED_ETH.times(eth_chf_price).times(seed_multiplier);


    // step 5
    // 2M - 50%
    // 6M - 15%
    if (amount_raised_chf <= MIN_SOFT_CAP_CHF) {
        future_round_percentage = multiplier.times(50);
    } else if (amount_raised_chf > MIN_SOFT_CAP_CHF && amount_raised_chf < SOFT_CAP_CHF) {
       future_round_percentage = uint(6750000000).minus((amount_raised_chf / 1000000).times(875000000));
    } else if (amount_raised_chf >= SOFT_CAP_CHF) {
        future_round_percentage = multiplier.times(15);
    }

    // step 6
    //percentage_of_three = 100*multiplier - FOUNDATION_PERCENTAGE*multiplier - TEAM_PERCENTAGE*multiplier - future_round_percentage;
    percentage_of_three = multiplier.times(100).minus(multiplier.times(FOUNDATION_PERCENTAGE)).minus(multiplier.times(TEAM_PERCENTAGE)).minus(future_round_percentage);

    // step 7
    earlybird_percentage = earlybird_coins.times(percentage_of_three) / (earlybird_coins.plus(regular_coins).plus(seed_coins));

    // step 8
    total_coins = multiplier.times(100).times(earlybird_coins) / earlybird_percentage;


    // step 9
    future_round_coins = future_round_percentage.times(total_coins) / 100 / multiplier;

    // step 10
    foundation_coins = FOUNDATION_PERCENTAGE.times(total_coins) / 100;

    // step 11
    team_coins = TEAM_PERCENTAGE.times(total_coins) / 100;

    // =======

    // seed coins to vault1 (no-lock) 1x
    seed_coins_vault1 = (seed_coins / seed_multiplier).times(multiplier);

    // seed coins to vault2 (with-lock) above 1x
    seed_coins_vault2 = seed_coins.minus((seed_coins / seed_multiplier).times(multiplier));

    // restore
    // Send to all the wallets (before dividing with multiplier?)

    if(future_round_coins > 0) {
      token.mint(futureRoundVault, future_round_coins);
    }

    if(foundation_coins > 0) {
      token.mint(foundationWallet, foundation_coins);
    }

    if(team_coins > 0) {
      token.mint(teamVault, team_coins);
    }

    if(seed_coins_vault1 > 0) {
      token.mint(seedVault1, seed_coins_vault1);
    }

    if(seed_coins_vault2 > 0) {
      token.mint(seedVault2, seed_coins_vault2);
    }

    // Then divide with multiplier
    //earlybird_coins = earlybird_coins / multiplier;
    //regular_coins = regular_coins / multiplier;
    //seed_coins = seed_coins / multiplier;
    //future_round_coins = future_round_coins / multiplier;
    //foundation_coins = foundation_coins / multiplier;
    //team_coins = team_coins / multiplier;
    //total_coins = total_coins / multiplier;
    //seed_coins_vault1 = seed_coins_vault1  / multiplier;
    //seed_coins_vault2 = seed_coins_vault2 / multiplier;
  }

  /// @dev Here you can set all the Vaults
  function setVaults(
    address _futureRoundVault,
    address _foundationWallet,
    address _teamVault,
    address _seedVault1,
    address _seedVault2
  ) onlyOwner {
    futureRoundVault = _futureRoundVault;
    foundationWallet = _foundationWallet;
    teamVault = _teamVault;
    seedVault1 = _seedVault1;
    seedVault2 = _seedVault2;
  }

  /* Can we run finalize properly */
  function isSane() public constant returns (bool) {
    // TODO: Check all vaults implement the correct vault interface
    return true;
  }

  function getDistributionFacts() public constant returns (uint chfRaised, uint chfRate) {
    uint _chfRate = mysteriumPricing.getEthChfPrice();
    return(crowdsale.weiRaised().times(_chfRate) / (10**18), _chfRate);
  }

  /** Called once by crowdsale finalize() if the sale was success. */
  function finalizeCrowdsale() {
    if(msg.sender == address(crowdsale) || msg.sender == owner) {
      // The owner can distribute tokens for testing and in emergency
      // Crowdsale distributes tokens at the end of the crowdsale
      var (chfRaised, chfRate) = getDistributionFacts();
      // distribute(chfRaised, chfRate);
    } else {
       throw;
    }
  }

}
