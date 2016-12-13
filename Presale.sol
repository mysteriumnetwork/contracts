// Mysterium Network Presale Smart Contract

pragma solidity ^0.4.6;

contract Presale {
    // TODO: external needed ?
    mapping (address => uint) public balances;
    
    // TODO: do we need counter ?
    //uint public balances_count = 0;
    uint public transfered_total = 0;
    
    uint public constant min_goal_amount = 2000 ether;
    uint public constant max_goal_amount = 6000 ether;
    
    // Mysterium project wallet
    address public project_wallet;

    uint public presale_start_block;
    uint public presale_end_block;
    
    uint public contract_deploy_date;
    
    function Presale(uint _start_block, uint _end_block, address _project_wallet) {
        if (_start_block <= block.number) throw;
        if (_end_block <= _start_block) throw;
        if (_project_wallet == 0) throw;
        
        presale_start_block = _start_block;
        presale_end_block = _end_block;
        project_wallet = _project_wallet;
	contract_deploy_date = now;
    }
	
    function has_presale_started() private constant returns (bool) {
	return block.number >= presale_start_block;
    }
    
    function has_presale_time_ended() private constant returns (bool) {
        return block.number > presale_end_block;
    }
    
    function is_min_goal_reached() private constant returns (bool) {
        return transfered_total >= min_goal_amount;
    }
    
    function is_max_goal_reached() private constant returns (bool) {
        return transfered_total > max_goal_amount;
    }
    
    // Accept ETH while presale is active or until maximum goal is reached.
    function () payable {
	// check if presale has started
        if (!has_presale_started()) throw;
	    
	// check if presale date is not over
	if (has_presale_time_ended()) throw;
	    
	// don`t accept transactions with zero value
	if (msg.value == 0) throw;
	    
	// set data
	balances[msg.sender] += msg.value;
	transfered_total += msg.value;
	    
	// TODO: do not count same balance twice
	//balances_count += 1;
	    
	// check if max goal is not reached
	if (is_max_goal_reached()) throw;
    }
    
    // Transfer ETH to Mysterium project wallet, as soon as minimum goal is reached.
    function transfer_funds_to_project() {
        if (!is_min_goal_reached()) throw;
        if (this.balance == 0) throw;
        
        // transfer ethers to Mysterium project wallet
        if (!project_wallet.send(this.balance)) throw;
    }
    
    // Refund ETH in case the minimum goal was not reached after presale end day.
    // Refund will be available for two months after presale end day.
    // ETH will be sent Mysterium project wallet in case anything left unclaimed after two months period.
    function refund() {
        if (!has_presale_time_ended()) throw;
        if (is_min_goal_reached()) throw;
        
        if (now - contract_deploy_date < 120 days) {
            var amount = balances[msg.sender];
            
            // check if sender has balance
            if (amount == 0) throw;
            
            // reset balance
            balances[msg.sender] = 0;
            
            // actual refund
            if (!msg.sender.send(amount)) throw;
            
        } else {
            if (this.balance == 0) throw;
            // transfer left ETH to Mysterium project wallet
            if (!project_wallet.send(this.balance)) throw;
        }
    }
}
