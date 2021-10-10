pragma solidity >0.5.0;

import "openzeppelin/contracts/token/ERC721/ERC721.sol";


contract ticketNFT is ERC721 {
    //https://www.youtube.com/watch?v=YxU87o4U5iw
    //https://www.youtube.com/watch?v=ZH_7nEIJDUY
    //https://docs.openzeppelin.com/contracts/2.x/api/token/erc721#ERC721Metadata-tokenURI-uint256-

    uint256 private tokenCounter; // counter for NFT
    uint256[] private ticketNFTid; // Store every Token Id created. With token id we can get the URI and the user.

    constructor () public ERC721("ticket","TICKEY"){
        tokenCounter = 0;
    }

    function createTicketNFT(string memory tokenURI) public returns(uint256){
        uint256 newItemId = tokenCounter;

        _safeMint(msg.sender, newItemId);
        _setTokenURI(newItemId, tokenURI);
        ticketNFTid.push(newItemId);
        tokenCounter = tokenCounter + 1;

        return newItemId;
    }

    function getAllTokenId() public view returns (uint256[]){
        // Returns the array of token id.
        return ticketNFTid;
    }

    function getOwner(uint256 memory tokenId) public view returns (address){
        // Returns the address of the owner of the given token id.
        return _ownerOf(tokenId);
    }

    function getTicketURI(uint256 memory tokenId) public view returns(string){
        // Returns the URI (metadata) of the nft with the given token id.
        return _tokenURI(tokenId);
    }

    // l'istanza di questo sc verrà richiamato da new_event per la creazione dei ticket nft, passandogli un testo in formato json
    // che contiene le informazioni relative al biglietto (nome ev, nome buyer, prezzo, data, tax seals, ecc).
    // si potrà accedere ai metadati con _tokenURI(tokenID).
    // DEPLOY: quando si avvia il sito
}
