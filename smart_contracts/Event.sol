pragma solidity >0.5.0;

contract Event {
  enum eventStates {available, cancelled, expired}

  string private name;
  string private date;
  eventStates state;
  uint256 private seatsPrice;
  string private artist;
  uint256 private availableSeats; // Actual available seats
  uint256 private initialAvailableSeats; // Store the initial amount of available seats
  mapping(address => uint256) private resellerSeatsList; // Store the address of the reseller and number of seats purchased


  constructor(string memory eventName, string memory eventDate, uint256 eventSeatsPrice, uint256 seats) public {
    setName(eventName);
    setDate(eventDate);
    setSeatsPrice(seats);
    setAvailableSeats(eventSeatsPrice);
    setAvailableState;
  }


  function setName(string memory eventName) public {
    name = eventName;
  }

  function getName() view public returns (string memory ) {
    return name;
  }


  function setAvailableState() public returns () {
    state = eventStates.available;
  }

  function setCancelledState() public returns () {
    state = eventStates.cancelled;
  }

  function setExpiredState() public returns () {
    state = eventStates.expired;
  }

  function getState() view public returns (evenStates) {
    return state;
  }


  function setArtist(string memory artistName) public returns () {
    artist = artistName;
  }

  function getArtist() view public returns () {
    return artist;
  }


  function setDate(string memory eventDate) public {
    date = eventDate;
  }

  function getDate() view public returns (string memory){
    return date;
  }


  function setSeatsPrice(uint256 eventSeatsPrice) public{
    seatsPrice = eventSeatsPrice;
  }

  function getSeatsPrice() view public returns (uint256) {
    return seatsPrice;
  }


  function setAvailableSeats(uint256 seats) public {
    require(seats >= 0, "Insufficient available seats!");
    availableSeats = seats;
    initialAvailableSeats = seats;
  }

  function getAvailableSeats() view public returns (uint256){
    return availableSeats;
  }


  function getReseller_seats(address memory reseller) view public returns (uint256){
   return resellerSeatsList[reseller];
  }


  function purchaseSeats(uint256 seatsPurchased) public {
    int256 remainder = get_availableSeats() - seatsPurchased;
    require(remainder >= 0, "Insufficient available seats!");

    // Check if the address exists in the map... Prove the validity of this method!
    if (resellerSeatsList[msg.sender] != int256(0x0)){
      uint256 actual_value = resellerSeatsList[msg.sender];
      resellerSeatsList[msg.sender] = actual_value + uint256(seatsPurchased);
    }
    else{
      resellerSeatsList[msg.sender] = uint256(seatsPurchased);
    }
    setAvailableSeats(uint256(remainder));
  }
}

