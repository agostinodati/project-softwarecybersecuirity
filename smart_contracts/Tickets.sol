pragma solidity >0.5.0;

import "./Event.sol";

contract TicketOffice {
    enum ticketStates {valid, cancelled, obliterated}

    uint256 private ticketCounter; // counter for
    address resellerAddress;
    address eventAddress;
    uint256 totalTickets;
    uint256 remainingTickets;
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

    constructor (address memory reseller, address memory eventAdr, uint256 seatsPurchased) public {
        ticketCounter = 0;
        resellerAddress = reseller;
        eventAddress = eventAdr;
        totalTickets = seatsPurchased;
        remainingTickets = seatsPurchased;
    }

    function createTicket(uint256 price, address memory buyer, string memory seal, string memory timestamp, ticketStates state) public returns(uint256) {
        if (getRemainingTickets() == 0) throw;

        Event eventPurchased = Event(eventAddress);
        uint256 id = ticketCounter;

        Ticket new_ticket = Ticket({
            ticketId: id,
            eventName: eventPurchased.getName(),
            ticketPrice: price,
            eventDate: eventPurchased.getDate(),
            buyerAddress: buyer,
            ticketSeal: seal,
            ticketTimestamp: timestamp,
            ticketState: state
        });
        tickets.push(new_ticket);
        ticketCounter = ticketCounter + 1;

        buyersTickets(buyer) = id;

        return id;
    }

    function getTicketIdByAddressBuyer(address memory buyerAddress) public view returns (string) {
        // Search in the map the ticket id of the buyer.
        string ticketId;
        if (buyersTickets[buyerAddress] != int256(0x0)){
            ticketId = buyersTickets[buyerAddress];
        }
        else{
            ticketId = "Ticket ID not found.";
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
}
