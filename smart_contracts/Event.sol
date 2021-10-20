pragma solidity >0.5.0;

contract Event {
  enum eventStates {available, cancelled, expired}
  eventStates state;
  string private name;
  string private date;

  string private artist;
  string private location;
  string private description;

  uint256 private seatsPrice;
  uint256 private availableSeats; // Actual available seats
  uint256 private initialAvailableSeats; // Store the initial amount of available seats
  mapping(address => uint256) private resellerSeatsList; // Store the address of the reseller and number of seats purchased

  constructor(string memory eventName, string memory eventDate, uint256 seats,  uint256 eventSeatsPrice,
    string memory eventArtist, string memory eventLocation, string memory eventDescription) public {
    setName(eventName);
    setDate(eventDate);
    setArtist(eventArtist);
    setLocation(eventLocation);
    setDescription(eventDescription);

    setSeatsPrice(eventSeatsPrice);
    setAvailableSeats(seats);
    setAvailableState;
  }

  function setArtist(string memory eventArtist) public {
    artist = eventArtist;
  }

  function getArtist() view public returns (string memory ) {
    return artist;
  }

  function setLocation(string memory eventLocation) public {
    location = eventLocation;
  }

  function getLocation() view public returns (string memory ) {
    return location;
  }

  function setDescription(string memory eventDescription) public {
    description = eventDescription;
  }

  function getDescription() view public returns (string memory ) {
    return description;
  }

  function setName(string memory eventName) public {
    name = eventName;
  }

  function getName() view public returns (string memory ) {
    return name;
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
    if (seats < 0) revert();

    availableSeats = seats;
    initialAvailableSeats = seats;
  }

  function getAvailableSeats() view public returns (uint256){
    return availableSeats;
  }

  function setAvailableState() public {
    state = eventStates.available;
  }

  function setCancelledState() public {
    state = eventStates.cancelled;
  }

  function setExpiredState() public {
    state = eventStates.expired;
  }

  function getState() view public returns (eventStates) {
    return state;
  }

  function getReseller_seats(address reseller) view public returns (uint256){
   return resellerSeatsList[reseller];
  }

  function purchaseSeats(uint256 seatsPurchased) public {
    uint256 remainder = getAvailableSeats() - seatsPurchased;
    if(remainder < 0) revert();

    // Check if the address exists in the map... Prove the validity of this method!
    if (resellerSeatsList[msg.sender] != uint256(0x0)){
      uint256 actual_value = resellerSeatsList[msg.sender];
      resellerSeatsList[msg.sender] = actual_value + uint256(seatsPurchased);
    }
    else{
      resellerSeatsList[msg.sender] = uint256(seatsPurchased);
    }
    setAvailableSeats(uint256(remainder));
  }
}

