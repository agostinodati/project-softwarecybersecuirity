pragma solidity >0.5.0;

import "./smart_contracts/Event.sol";

contract TicketOffice {
    enum ticketStates {valid, cancelled, obliterated}

    uint256 private ticketCounter; // counter for

    address resellerAddress;

    address eventAddress;
    uint256 totalTickets;
    uint256 remainingTickets;
    uint256 ticketsPrice;
    mapping(address => uint256) buyersTickets; // Map to store the purchase of buyers.

    struct Ticket {
        uint ticketId;
        string eventName;
        uint ticketPrice;
        string eventDate;
        address buyerAddress;
        string ticketSeal; // this is an hash of buyer's and event's information
        string ticketTimestamp;
        ticketStates ticketState;
    }

    Ticket[] tickets;

    constructor (address reseller, address eventAdr, uint price, uint seats_purchase) public {
        Event eventPurchased = Event(eventAdr);
        ticketCounter = 1;
        setResellerAdd(reseller);
        //resellerAddress = reseller;
        setEventAdd(eventAdr);
        //eventAddress = eventAdr;

        //totalTickets = eventPurchased.getReseller_seats(reseller);
        //remainingTickets = eventPurchased.getAvailableSeats();

        setRemainingTickets(seats_purchase);
        //ticketsPrice = price;
        setTicketsPrice(price);
    }

    function createTicket(address buyer, string memory seal,
        string memory timestamp) public returns(uint256) {
        if (getRemainingTickets() == 0) revert();

        Event eventPurchased = Event(eventAddress);
        uint256 id = ticketCounter;

        Ticket memory new_ticket = Ticket({
            ticketId: id,
            eventName: eventPurchased.getName(),
            ticketPrice: getTicketsPrice(),
            eventDate: eventPurchased.getDate(),
            buyerAddress: buyer,
            ticketSeal: seal,
            ticketTimestamp: timestamp,
            ticketState: ticketStates.valid
        });
        tickets.push(new_ticket);
        ticketCounter = ticketCounter + 1;

        remainingTickets = remainingTickets - 1;

        buyersTickets[buyer] = id;

        return id;
    }

    function setResellerAdd(address reseller) public {
        resellerAddress = reseller;
    }

    function getResellerAdd() public view returns (address){
        return resellerAddress;
    }

    function setEventAdd(address eventAdr) public {
        eventAddress = eventAdr;
    }

    function getEventAdd() public view returns (address){
        return eventAddress;
    }

    function setTicketsPrice(uint price) public {
        ticketsPrice = price;
    }

    function getTicketsPrice() public view returns (uint){
        return ticketsPrice;
    }

    function getTicketIdByAddressBuyer(address buyerAddress) public view returns (uint256) {
        // Search in the map the ticket id of the buyer.
        uint256 ticketId;
        if (buyersTickets[buyerAddress] != uint256(0x0)){
            ticketId = buyersTickets[buyerAddress];
        }
        else{
            ticketId = 0;
        }
        return ticketId;
    }

    function getOwner(uint256 ticketId) public view returns (address) {
        // Returns the address of the owner of the given ticket id.
        return tickets[ticketId].buyerAddress;
    }

    function getState(uint256 ticketId) public view returns (ticketStates) {
        // Get the state of the ticket.
        return tickets[ticketId].ticketState;
    }

    function getRemainingTickets() public view returns (uint256) {
        // Get the number of available tickets.
        return remainingTickets;
    }

    function setRemainingTickets(uint256 tickets) public {
        require(tickets >= 0, "Insufficient available tickets!");
        remainingTickets = tickets;
  }

    function getBuyer_seats(address buyer) view public returns (uint256){
        return buyersTickets[buyer];
    }

    function purchaseTicket(uint256 ticketPurchased) public {
        uint256 ticketLeft = getRemainingTickets() - ticketPurchased;
        require(ticketLeft >= 0, "Insufficient available ticket!");

        // Check if the address exists in the map... Prove the validity of this method!
        if (buyersTickets[msg.sender] != uint256(0x0)){
          uint256 actual_value = buyersTickets[msg.sender];
          buyersTickets[msg.sender] = actual_value + uint256(ticketPurchased);
        }
        else{
          buyersTickets[msg.sender] = uint256(ticketPurchased);
        }
        setRemainingTickets(uint256(ticketLeft));
    }
}