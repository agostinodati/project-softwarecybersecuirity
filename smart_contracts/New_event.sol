pragma solidity >0.5.0;

contract new_event{

  string private name;
  string private date;
  int256 private available_seats;
  int256 private initial_available_seats;
  mapping(address => int256) private reseller_seats_list;
  mapping(address => int256) private buyer_ticket_list;

  constructor(string memory x, string memory y, int256 z) public {
                       name = x;
                       date = y;
                       available_seats = z;
                       initial_available_seats = z;
  }

  function set_name(string memory x) public {
    name = x;
  }

  function set_date(string memory x) public {
    date = x;
  }

  function get_reseller_seats(address reseller) view public returns (int256){
   return reseller_seats_list[reseller];
  }

  function get_name() view public returns (string memory ){
    return name;
  }

  function get_date() view public returns (string memory){
    return date;
  }

  function get_available_seats() view public returns (int256){
    return available_seats;
  }

  function set_available_seats(int256 num) public {
    require(num >= 0, "Insufficient available seats!");
    available_seats = num;
  }

  function purchase_seats(int256 seats_bought) public {
    int256 remainder = get_available_seats() - seats_bought;
    require(remainder > 0);
    reseller_seats_list[msg.sender] = int256(seats_bought);
    set_available_seats(remainder);
  }
}