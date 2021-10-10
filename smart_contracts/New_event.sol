pragma solidity >0.5.0;

contract new_event{

  string private name;
  string private date;
  uint256 private seats_price;
  uint256 private available_seats; // Actual available seats
  uint256 private initial_available_seats; // Store the initial amount of available seats
  mapping(address => uint256) private reseller_seats_list; // Store the address of the reseller and number of seats purchased

  uint256[] private ticketsNFTid; // Store the
  uint256 private ticketsNFTcounter;

  constructor(string memory x, string memory y, uint256 z, uint256 k) public {
                       set_name(x);
                       set_date(y);
                       set_seats_price(k);
                       set_available_seats(z);
  }


  function set_name(string memory x) public {
    name = x;
  }

  function get_name() view public returns (string memory ){
    return name;
  }


  function set_date(string memory x) public {
    date = x;
  }

  function get_date() view public returns (string memory){
    return date;
  }


  function set_seats_price(uint256 memory x) public{
    seats_price = x;
  }

  function get_seats_price() view public returns (uint256) {
    return seats_price;
}


  function set_available_seats(uint256 x) public {
    require(x >= 0, "Insufficient available seats!");
    available_seats = x;
    initial_available_seats = x;
  }

  function get_available_seats() view public returns (uint256){
    return available_seats;
  }


  function get_reseller_seats(address reseller) view public returns (uint256){
   return reseller_seats_list[reseller];
  }


  function purchase_seats(uint256 seats_purchased) public {
    int256 remainder = get_available_seats() - seats_purchased;
    require(remainder >= 0, "Insufficient available seats!");

    // Check if the address exists... Prove the validity of this method!
    if (reseller_seats_list[msg.sender] != int256(0x0)){
      uint256 actual_value = reseller_seats_list[msg.sender];
      reseller_seats_list[msg.sender] = actual_value + uint256(seats_purchased);
    }
    else{
      reseller_seats_list[msg.sender] = uint256(seats_purchased);
    }
    set_available_seats(uint256(remainder));
  }
}

