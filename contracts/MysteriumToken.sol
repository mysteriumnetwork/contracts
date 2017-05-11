pragma solidity ^0.4.7;

import "./CrowdsaleToken.sol";

contract MysteriumToken is CrowdsaleToken {
  function MysteriumToken(string _name, string _symbol, uint _initialSupply, uint _decimals)
   CrowdsaleToken(_name, _symbol, _initialSupply, _decimals) {
  }
}
