pragma solidity ^0.4.7;

import "./MintedTokenCappedCrowdsale.sol";

contract MysteriumCrowdsale is MintedTokenCappedCrowdsale {

  function MysteriumCrowdsale(address _token, PricingStrategy _pricingStrategy, address _multisigWallet, uint _start, uint _end, uint _minimumFundingGoal, uint _maximumSellableTokens)
    MintedTokenCappedCrowdsale(_token, _pricingStrategy, _multisigWallet, _start, _end, _minimumFundingGoal, _maximumSellableTokens) {}

  using SafeMathLib for uint;

  // testable variables
  uint public earlybird_coins;
  uint public regular_coins;
  uint public seed_coins;
  uint public total_coins;
  uint public future_round_coins;
  uint public foundation_coins;
  uint public team_coins;
  uint public seed_coins_vault1;
  uint public seed_coins_vault2;


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

    //restore
    earlybird_coins = earlybird_coins / multiplier;
    regular_coins = regular_coins / multiplier;
    seed_coins = seed_coins / multiplier;
    future_round_coins = future_round_coins / multiplier;
    foundation_coins = foundation_coins / multiplier;
    team_coins = team_coins / multiplier;
    total_coins = total_coins / multiplier;
    seed_coins_vault1 = seed_coins_vault1  / multiplier;
    seed_coins_vault2 = seed_coins_vault2 / multiplier;

  }


}
