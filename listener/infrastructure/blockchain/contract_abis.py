"""
📜 Smart Contract ABIs
ABIs برای Solidity contracts
"""

# Factory Contract ABI (events و functions مورد نیاز)
BONDING_CURVE_FACTORY_ABI = [
    # Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenAddress", "type": "address"},
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "name", "type": "string"},
            {"indexed": False, "name": "symbol", "type": "string"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "TokenApprovedForDeployment",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenAddress", "type": "address"},
            {"indexed": True, "name": "curveAddress", "type": "address"},
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "name", "type": "string"},
            {"indexed": False, "name": "symbol", "type": "string"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "BondingCurveDeployed",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenAddress", "type": "address"},
            {"indexed": False, "name": "isActive", "type": "bool"}
        ],
        "name": "CurveStatusChanged",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "RegularTokenCreatorApproved",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "RegularTokenCreatorRevoked",
        "type": "event"
    },
    
    # View Functions
    {
        "inputs": [],
        "name": "getAllTokens",
        "outputs": [
            {
                "components": [
                    {"name": "tokenAddress", "type": "address"},
                    {"name": "creator", "type": "address"},
                    {"name": "curveAddress", "type": "address"},
                    {"name": "name", "type": "string"},
                    {"name": "symbol", "type": "string"},
                    {"name": "deployedAt", "type": "uint256"},
                    {"name": "isActive", "type": "bool"},
                    {"name": "isApproved", "type": "bool"}
                ],
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getDeployedCurves",
        "outputs": [
            {
                "components": [
                    {"name": "tokenAddress", "type": "address"},
                    {"name": "creator", "type": "address"},
                    {"name": "curveAddress", "type": "address"},
                    {"name": "name", "type": "string"},
                    {"name": "symbol", "type": "string"},
                    {"name": "deployedAt", "type": "uint256"},
                    {"name": "isActive", "type": "bool"},
                    {"name": "isApproved", "type": "bool"}
                ],
                "name": "",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Individual Bonding Curve Contract ABI
INDIVIDUAL_BONDING_CURVE_ABI = [
    # Main Trade Event
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": True, "name": "isBuy", "type": "bool"},
            {"indexed": False, "name": "ethInOrOut", "type": "uint256"},
            {"indexed": False, "name": "tokenDelta", "type": "uint256"},
            {"indexed": False, "name": "priceBefore", "type": "uint256"},
            {"indexed": False, "name": "priceAfter", "type": "uint256"},
            {"indexed": False, "name": "supplyAfter", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "Trade",
        "type": "event"
    },
    
    # Enhanced Trading Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "buyer", "type": "address"},
            {"indexed": False, "name": "tokensReceived", "type": "uint256"},
            {"indexed": False, "name": "ethSpent", "type": "uint256"},
            {"indexed": False, "name": "platformFee", "type": "uint256"},
            {"indexed": False, "name": "creatorFee", "type": "uint256"},
            {"indexed": False, "name": "newPrice", "type": "uint256"}
        ],
        "name": "TokensPurchased",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "seller", "type": "address"},
            {"indexed": False, "name": "tokenAmount", "type": "uint256"},
            {"indexed": False, "name": "ethReceived", "type": "uint256"},
            {"indexed": False, "name": "platformFee", "type": "uint256"},
            {"indexed": False, "name": "creatorFee", "type": "uint256"},
            {"indexed": False, "name": "newPrice", "type": "uint256"}
        ],
        "name": "TokensSold",
        "type": "event"
    },
    
    # Fee Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "platformFee", "type": "uint256"},
            {"indexed": False, "name": "creatorFee", "type": "uint256"},
            {"indexed": False, "name": "tradeId", "type": "uint256"}
        ],
        "name": "FeesAccrued",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "kind", "type": "string"}
        ],
        "name": "FeesTransferred",
        "type": "event"
    },
    
    # Lifecycle Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "bridgedAmount", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "Initialized",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "TokensBridged",
        "type": "event"
    },
    
    # Milestone Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "level", "type": "uint256"},
            {"indexed": False, "name": "reserveETH", "type": "uint256"},
            {"indexed": False, "name": "vestedTokens", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "MilestoneReached",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "CreatorTokensClaimed",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "mcapOrReserves", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "ReadyForDEX",
        "type": "event"
    },
    
    # Migration Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": False, "name": "reserveETH", "type": "uint256"},
            {"indexed": False, "name": "tokenAmount", "type": "uint256"},
            {"indexed": False, "name": "targetDEX", "type": "address"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "MigrationStarted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "pool", "type": "address"},
            {"indexed": False, "name": "tokenId", "type": "uint256"},
            {"indexed": False, "name": "ethUsed", "type": "uint256"},
            {"indexed": False, "name": "tokenUsed", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "MigrationCompleted",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "tokenAddress", "type": "address"},
            {"indexed": True, "name": "poolAddress", "type": "address"},
            {"indexed": False, "name": "tokenAmount", "type": "uint256"},
            {"indexed": False, "name": "ethAmount", "type": "uint256"},
            {"indexed": False, "name": "tokenId", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "MigratedToUniswap",
        "type": "event"
    },
    
    # Security Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "user", "type": "address"},
            {"indexed": False, "name": "attemptedAmount", "type": "uint256"},
            {"indexed": False, "name": "maxAllowed", "type": "uint256"},
            {"indexed": False, "name": "reason", "type": "string"}
        ],
        "name": "LargeTradeBlocked",
        "type": "event"
    },
    
    # View Functions
    {
        "inputs": [],
        "name": "calculatePrice",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "tokenAmount", "type": "uint256"}],
        "name": "calculateBuyCost",
        "outputs": [{"name": "totalCost", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "ethAmount", "type": "uint256"}],
        "name": "calculateTokensFromEth",
        "outputs": [{"name": "tokenAmount", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "state",
        "outputs": [
            {"name": "bridgedAmount", "type": "uint128"},
            {"name": "tokensSold", "type": "uint128"},
            {"name": "reserveBalance", "type": "uint96"},
            {"name": "createdAt", "type": "uint64"},
            {"name": "isInitialized", "type": "bool"},
            {"name": "isApprovedForDeployment", "type": "bool"},
            {"name": "isReadyForDEX", "type": "bool"},
            {"name": "isMigratedToUniswap", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "creator",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "tokenName",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "tokenSymbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getContractStats",
        "outputs": [
            {"name": "currentReserves", "type": "uint256"},
            {"name": "tokensSoldSoFar", "type": "uint256"},
            {"name": "availableTokens", "type": "uint256"},
            {"name": "currentPrice", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# ERC20 Token ABI (برای FanToken و سایر tokens)
ERC20_ABI = [
    # Standard ERC20 Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Transfer",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "owner", "type": "address"},
            {"indexed": True, "name": "spender", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"}
        ],
        "name": "Approval",
        "type": "event"
    },
    
    # Standard ERC20 Functions
    {
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Fan Token ABI (اضافه بر ERC20)
FAN_TOKEN_ABI = ERC20_ABI + [
    # Fan Token Specific Events
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "totalBurned", "type": "uint256"},
            {"indexed": False, "name": "reason", "type": "string"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "CommunityBurn",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "amount", "type": "uint256"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "CreatorClaim",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "creator", "type": "address"},
            {"indexed": False, "name": "metadataURI", "type": "string"},
            {"indexed": False, "name": "timestamp", "type": "uint256"}
        ],
        "name": "MetadataUpdated",
        "type": "event"
    },
    
    # Fan Token Specific Functions
    {
        "inputs": [],
        "name": "creator",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "bondingCurve",
        "outputs": [{"name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "metadataURI",
        "outputs": [{"name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalBurned",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Event signatures برای filtering
EVENT_SIGNATURES = {
    # Factory Events
    'BondingCurveDeployed': '0x7d84a6263ae0d98d3329bd7b46bb4e8d6f98cd35a7adb45c274c8b7fd5ebd5e0',
    'TokenApprovedForDeployment': '0xa7b5a90eab3daadc7e9c3b1b8c7e0f2d3c6b9e8a4d5e7f1a2b3c4d5e6f7a8b9c0',
    
    # Bonding Curve Events  
    'Trade': '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67',
    'TokensPurchased': '0x8b73e5b2c6d1e3f0a5b8c2d1e4f3b2a1e5d4c3b2f1e0d9c8b7a6e5f4c3b2a1e0',
    'TokensSold': '0xf1e2d3c4b5a69e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b',
    'FeesAccrued': '0xa1b2c3d4e5f69e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6',
    'MilestoneReached': '0xd1e2f3a4b5c69e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c',
    'MigratedToUniswap': '0xe1f2a3b4c5d69e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7',
    
    # ERC20 Events
    'Transfer': '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef',
    'Approval': '0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925',
    
    # Fan Token Events
    'CommunityBurn': '0xb1c2d3e4f5a69e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c',
    'CreatorClaim': '0xc1d2e3f4a5b69e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7',
    'MetadataUpdated': '0xd1e2f3a4b5c69e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d7c6b5a49e8d'
}

# Helper function برای دریافت event signature
def get_event_signature(event_name: str) -> str:
    """دریافت signature یک event"""
    return EVENT_SIGNATURES.get(event_name, '')

# Helper function برای تشخیص نوع contract
def get_contract_abi(contract_type: str) -> list:
    """دریافت ABI بر اساس نوع contract"""
    if contract_type == 'factory':
        return BONDING_CURVE_FACTORY_ABI
    elif contract_type == 'bonding_curve':
        return INDIVIDUAL_BONDING_CURVE_ABI
    elif contract_type == 'fan_token':
        return FAN_TOKEN_ABI
    elif contract_type == 'erc20':
        return ERC20_ABI
    else:
        return []
