# hardcode constants to smart contract
SOFT_CAP = 6000000
MIN_SOFT_CAP = 2000000
SEED_RAISED_ETH = 6000
FOUNDATION_PERCENTAGE = 9
TEAM_PERCENTAGE = 10

# set parameter before Token Sale
eth_price_chf = 88

# smart contract knows this value after raising is finished
amount_raised_chf = 6000000



# step 1, E6: Calculate "EarlyBird" coins (1chf = 1.2 myst), based on C10
if amount_raised_chf <= SOFT_CAP:
    earlybird_coins = amount_raised_chf * 1.2
else:
    earlybird_coins = SOFT_CAP * 1.2

print 'Early Bird Coins: {}'.format(earlybird_coins)


# step 2, F6: Calculate Regular investor coins (1chf = 1myst), based on C11
regular_coins = 0
if amount_raised_chf > SOFT_CAP:
    regular_coins = (amount_raised_chf - SOFT_CAP) * 1

print 'Regular Coins: {}'.format(regular_coins)


# step 3, G5: Define Seed MULTIPLIER, based on C8 - raised amount during ICO
# 2M - 1x
# 6M - 5x
if amount_raised_chf <= MIN_SOFT_CAP:
    seed_multiplier = 1
elif amount_raised_chf > MIN_SOFT_CAP and amount_raised_chf < SOFT_CAP:
    seed_multiplier = amount_raised_chf / 1000000.0 - 1
elif amount_raised_chf >= SOFT_CAP:
    seed_multiplier = 5

print 'Seed Multiplier: {}x'.format(seed_multiplier)


# step 4, G6: Calculate Seed Round Tokens using G5
seed_coins = SEED_RAISED_ETH * eth_price_chf * seed_multiplier
print 'Seed Coins: {}'.format(seed_coins)


# step 5, H3: Calculate PERCENTAGE of "tokens reserved for II'nd round", using C8
# 2M - 50%
# 6M - 15%
if amount_raised_chf <= MIN_SOFT_CAP:
    future_round_percentage = 50
elif amount_raised_chf > MIN_SOFT_CAP and amount_raised_chf < SOFT_CAP:
    # calculate proportionally
    # y = 67.5 - 8.75x
    future_round_percentage = 67.5 - 8.75 * (amount_raised_chf / 1000000.0)
elif amount_raised_chf >= SOFT_CAP:
    future_round_percentage = 15

print 'Future reserved Coins percentage: {}%'.format(future_round_percentage)


# step 6, E2: Calculate PERENTAGE of  (Early bird + Regular + Seed) = 100% - Team(10%) - Foundation (9%) - II'nd round(H3)
percentage_of_three = 100 - FOUNDATION_PERCENTAGE - TEAM_PERCENTAGE - future_round_percentage
print 'Percentage of (Early bird + Regular + Seed): {}%'.format(percentage_of_three)


# step 7, E3,knowing total percentage E2 and total coins for (EarlyBird, Regular and Seed) = sum(E3:G3)
earlybird_percentage = earlybird_coins * percentage_of_three / (earlybird_coins+regular_coins+seed_coins)
print 'Early bird  percentage: {}%'.format(earlybird_percentage)


# step 8, K6: Calculate TOTAL coins knowing E3 & E6
total_coins = earlybird_coins * 100 / earlybird_percentage
print 'Total coins: {}'.format(total_coins)


# step 9, H6: Calculate II'nd round coins using K6 and H3
future_round_coins = future_round_percentage * total_coins / 100
print 'Future round coins: {}'.format(future_round_coins)


# step 10, I6: Calculate Foundation coins using K6 and I3
foundation_coins = FOUNDATION_PERCENTAGE * total_coins / 100
print 'Foundation coins: {}'.format(foundation_coins)


# step 11, J6: Calculate Team coins using K6 and J3
team_coins = TEAM_PERCENTAGE * total_coins / 100
print 'Team coins: {}'.format(team_coins)

