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

  uint public allocatedBonus;
  uint public bonusBasePoints;

  MysteriumPricing mysteriumPricing;

  // Vaults:
  address earlybirdVault;
  address regularVault;
  address seedVault;
  address futureRoundVault;
  address foundationVault;
  address teamVault;
  address seedVault1;
  address seedVault2;

  function MysteriumTokenDistribution(CrowdsaleToken _token, Crowdsale _crowdsale, MysteriumPricing _mysteriumPricing, address _teamMultisig, uint _bonusBasePoints) {
    token = _token;
    crowdsale = _crowdsale;
    if(address(crowdsale) == 0) {
      throw;
    }

    teamMultisig = _teamMultisig;
    if(address(teamMultisig) == 0) {
      throw;
    }

    mysteriumPricing = _mysteriumPricing;
    bonusBasePoints = _bonusBasePoints;
  }

  function distribute(uint amount_raised_chf, uint eth_chf_price) {
    // Distribute:
    // seed coins
    // foundation coins
    // team coins

    // constants
    uint SOFT_CAP_CHF = 6000000;
    uint MIN_SOFT_CAP_CHF = 2000000;
    uint SEED_RAISED_ETH = 6000;
    uint FOUNDATION_PERCENTAGE = 9;
    uint TEAM_PERCENTAGE = 10;
    //uint public EARLYBIRD_PRICE_MULTIPLIER = 1.2;
    uint REGULAR_PRICE_MULTIPLIER = 1;

    uint seed_multiplier;
    uint future_round_percentage;
    uint percentage_of_three;
    uint earlybird_percentage;

    uint multiplier = 10 ** 8;

    uint earlybird_coins;
    uint regular_coins;
    uint seed_coins;
    uint total_coins;
    uint future_round_coins;
    uint foundation_coins;
    uint team_coins;
    uint seed_coins_vault1;
    uint seed_coins_vault2;


    // step 1
    if (amount_raised_chf <= SOFT_CAP_CHF) {
       earlybird_coins = amount_raised_chf*multiplier + amount_raised_chf*multiplier/5;
    }
    else {
      earlybird_coins = SOFT_CAP_CHF*multiplier + SOFT_CAP_CHF*multiplier/5;
    }

    // step 2
    regular_coins = 0;
    if (amount_raised_chf > SOFT_CAP_CHF) {
      regular_coins = (amount_raised_chf - SOFT_CAP_CHF) * multiplier * REGULAR_PRICE_MULTIPLIER;
    }

    // step 3
    // 2M - 1x
    // 6M - 5x
    if (amount_raised_chf <= MIN_SOFT_CAP_CHF) {
        seed_multiplier = 1 * multiplier;
    } else if (amount_raised_chf > MIN_SOFT_CAP_CHF && amount_raised_chf < SOFT_CAP_CHF) {
        seed_multiplier = (amount_raised_chf / 1000000 - 1) * multiplier;

    } else if (amount_raised_chf >= SOFT_CAP_CHF) {
        seed_multiplier = 5 * multiplier;
    }

    // step 4
    seed_coins = SEED_RAISED_ETH * eth_chf_price * seed_multiplier;

    // step 5
    // 2M - 50%
    // 6M - 15%
    if (amount_raised_chf <= MIN_SOFT_CAP_CHF) {
        future_round_percentage = 50 * multiplier;
    } else if (amount_raised_chf > MIN_SOFT_CAP_CHF && amount_raised_chf < SOFT_CAP_CHF) {
       future_round_percentage = 6750000000 - 875000000 * (amount_raised_chf / 1000000);
    } else if (amount_raised_chf >= SOFT_CAP_CHF) {
        future_round_percentage = 15 * multiplier;
    }

    // step 6
    percentage_of_three = 100*multiplier - FOUNDATION_PERCENTAGE*multiplier - TEAM_PERCENTAGE*multiplier - future_round_percentage;

    // step 7
    earlybird_percentage = earlybird_coins * percentage_of_three / (earlybird_coins+regular_coins+seed_coins);

    // step 8
    total_coins = earlybird_coins * 100 * multiplier / earlybird_percentage;

    // step 9
    future_round_coins = future_round_percentage * total_coins / 100 / multiplier;

    // step 10
    foundation_coins = FOUNDATION_PERCENTAGE * total_coins / 100;

    // step 11
    team_coins = TEAM_PERCENTAGE * total_coins / 100;

    // =======

    // seed coins to vault1 (no-lock) 1x
    seed_coins_vault1 = seed_coins / seed_multiplier * multiplier;

    // seed coins to vault2 (with-lock) above 1x
    seed_coins_vault2 = seed_coins - seed_coins / seed_multiplier * multiplier;

    // restore
    // Send to all the wallets (before dividing with multiplier?)
    token.mint(earlybirdVault, earlybird_coins);
    token.mint(regularVault, regular_coins);
    token.mint(seedVault, seed_coins);
    token.mint(futureRoundVault, future_round_coins);
    token.mint(foundationVault, foundation_coins);
    token.mint(teamVault, team_coins);
    token.mint(seedVault1, seed_coins_vault1);
    token.mint(seedVault2, seed_coins_vault2);

    // Make token transferable
    token.releaseTokenTransfer();

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
  function setVaults(address _earlybirdVault,
    address _regularVault,
    address _seedVault,
    address _futureRoundVault,
    address _foundationVault,
    address _teamVault,
    address _seedVault1,
    address _seedVault2
  ) onlyOwner {
    earlybirdVault = _earlybirdVault;
    regularVault = _regularVault;
    seedVault = _seedVault;
    futureRoundVault = _futureRoundVault;
    foundationVault = _foundationVault;
    teamVault = _teamVault;
    seedVault1 = _seedVault1;
    seedVault2 = _seedVault2;
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

    uint chfRate = mysteriumPricing.chfRate();
    distribute(crowdsale.weiRaised()/chfRate, chfRate);

    // How many % of tokens the founders and others get, is this obsolete?
    //uint tokensSold = crowdsale.tokensSold();
    //allocatedBonus = tokensSold.times(bonusBasePoints) / 10000;
  }

}
