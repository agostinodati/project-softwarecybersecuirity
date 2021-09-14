pragma solidity >0.5.0;
// SPDX-License-Identifier: AFL-3.0
contract new_event{

  string private name;
  string private date;
  int256 private available_seats;
  address[] seats_buyers;

  constructor(string memory x, string memory y, int256 z) public {
                       name = x;
                       date = y;
                       available_seats = z;
  }

  function get_name() public view returns (string memory){
    return name;
  }

  function get_date() public view returns (string memory){
    return date;
  }

  function get_available_seats() public view returns (int256){
    return available_seats;
  }

  function set_available_seats(int256 num) public {
    require(num >= 0, "Insufficient available seats!");
    available_seats = num;
  }

  function buy_seats(int256 seats_bought) public {
    int256 remainder = get_available_seats() - seats_bought;
    require(remainder >= 0);
    this.set_available_seats(remainder);
  }
}