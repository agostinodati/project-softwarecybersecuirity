//pragma solidity >0.5.0;
pragma experimental ABIEncoderV2;

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
        setEventAdd(eventAdr);
        setTotalTickets(seats_purchase);
        setRemainingTickets(seats_purchase);
        setTicketsPrice(price);
    }

    function purchaseTicket(address buyer, string memory seal, string memory timestamp) public {
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
        uint256 id = ticketId-1;
        return tickets[id].buyerAddress;
    }

    function getState(uint256 ticketId) public view returns (string memory) {
        uint256 id = ticketId-1;
        ticketStates currentState = tickets[id].ticketState;
        string memory state;

        if (currentState==ticketStates.valid) state = "valid";
        if (currentState==ticketStates.cancelled) state = "cancelled";
        if (currentState==ticketStates.obliterated) state = "obliterated";

        return state;
    }

    function getSeal(uint256 ticketId) public view returns (string memory) {
        uint256 id = ticketId-1;
        return tickets[id].ticketSeal;
    }

    function getPurchaseTimestamp(uint256 ticketId) public view returns (string memory) {
        uint256 id = ticketId-1;
        return tickets[id].ticketTimestamp;
    }

    function getRemainingTickets() public view returns (uint256) {
        // Get the number of available tickets.
        return remainingTickets;
    }

    function setTotalTickets(uint256 tickets) public {
        if (tickets <= 0) revert();
        totalTickets = tickets;
    }

    function setRemainingTickets(uint256 tickets) public {
        if (tickets <= 0) revert();
        remainingTickets = tickets;
    }

    function modifyTicketNumber(uint256 tickets) public {
        if (tickets <= 0) revert();
        totalTickets = totalTickets + tickets;
        remainingTickets = remainingTickets + tickets;
    }

    function getBuyer_seats(address buyer) view public returns (uint256){
        return buyersTickets[buyer];
    }

    function setValidState(uint256 id) public {
        uint256 ticketId = id -1;
        tickets[ticketId].ticketState = ticketStates.valid;
    }

    function setCancelledState(uint256 id) public {
        uint256 ticketId = id -1;
        tickets[ticketId].ticketState = ticketStates.cancelled;
    }

    function setObliteratedState(uint256 id) public {
        uint256 ticketId = id -1;
        tickets[ticketId].ticketState = ticketStates.obliterated;
    }
}