"""
⛓️ Blockchain Service Implementation  
WebSocket connection به blockchain برای event listening
"""
import asyncio
import json
from typing import Dict, Any, Optional, AsyncIterator, List, Tuple
from decimal import Decimal
from web3 import AsyncWeb3, Web3
from web3.providers.persistent import WebSocketProvider
from web3.contract import AsyncContract
from web3.types import LogReceipt, FilterParams, BlockIdentifier
from loguru import logger

from ...application.interfaces import IBlockchainService
from ...config.settings import Settings
from ...domain.value_objects import TokenAddress
from .contract_abis import BONDING_CURVE_FACTORY_ABI, INDIVIDUAL_BONDING_CURVE_ABI


class BlockchainService(IBlockchainService):
    """Blockchain service for interacting with Ethereum/Hardhat"""
    
    def __init__(self, settings: Settings):
        self.settings = settings.blockchain
        self._w3: Optional[AsyncWeb3] = None
        self._ws_provider: Optional[WebSocketProvider] = None
        self._is_connected = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = self.settings.max_reconnection_attempts
        
        # Contract instances
        self._factory_contract: Optional[AsyncContract] = None
        self._curve_contracts: Dict[str, AsyncContract] = {}
        
        # Event filters
        self._event_filters: List[Any] = []
        
        # Stats
        self._events_received = 0
        self._last_block_number = 0
    
    async def connect(self) -> None:
        """Connect to blockchain"""
        try:
            logger.info(f"🔗 Connecting to blockchain: {self.settings.ws_url}")
            
            # Create WebSocket provider
            self._ws_provider = WebSocketProvider(self.settings.ws_url)
            self._w3 = AsyncWeb3(self._ws_provider)
            
            # Initialize connection
            await self._w3.provider.connect()
            
            # Test connection
            await self._test_connection()
            
            # Setup factory contract (only if address is configured)
            if self.settings.factory_address:
                try:
                    await self._setup_factory_contract()
                    # Discover existing bonding curves
                    await self._discover_existing_curves()
                except Exception as e:
                    logger.warning(f"⚠️ Factory contract setup failed: {e}")
            else:
                logger.info("ℹ️ Factory address not configured, skipping contract setup")
            
            self._is_connected = True
            self._reconnect_attempts = 0
            
            logger.info("✅ Blockchain connection established")
            
        except Exception as e:
            logger.error(f"❌ Blockchain connection failed: {e}")
            self._is_connected = False
            raise
    
    async def _test_connection(self) -> None:
        """Test connection"""
        if not self._w3:
            raise Exception("Web3 instance not initialized")
        
        # Get latest block
        latest_block = await self._w3.eth.get_block('latest')
        self._last_block_number = latest_block['number']
        
        # Verify chain ID
        chain_id = await self._w3.eth.chain_id
        if chain_id != self.settings.chain_id:
            logger.warning(f"⚠️ Chain ID mismatch: expected {self.settings.chain_id}, got {chain_id}")
        
        logger.info(f"🔗 Connected to chain {chain_id}, latest block: {self._last_block_number}")
    
    async def _setup_factory_contract(self) -> None:
        """Setup factory contract"""
        if not self.settings.factory_address or not self._w3:
            raise Exception("Factory address not configured or Web3 not initialized")
        
        try:
            self._factory_contract = self._w3.eth.contract(
                address=Web3.to_checksum_address(self.settings.factory_address),
                abi=BONDING_CURVE_FACTORY_ABI
            )
            
            # Test contract call
            await self._factory_contract.functions.getAllTokens().call()
            
            logger.info(f"🏭 Factory contract setup: {self.settings.factory_address}")
            
        except Exception as e:
            logger.error(f"Failed to setup factory contract: {e}")
            raise
    
    async def _discover_existing_curves(self) -> None:
        """پیدا کردن bonding curves موجود"""
        if not self._factory_contract:
            return
        
        try:
            logger.info("🔍 Discovering existing bonding curves...")
            
            # Get all deployed curves
            deployed_curves = await self._factory_contract.functions.getDeployedCurves().call()
            
            logger.info(f"📊 Found {len(deployed_curves)} existing bonding curves")
            
            # Setup contracts for each curve
            for curve_info in deployed_curves:
                curve_address = curve_info[2]  # curveAddress field
                await self._add_curve_contract(curve_address)
            
        except Exception as e:
            logger.error(f"Failed to discover existing curves: {e}")
    
    async def _add_curve_contract(self, curve_address: str) -> None:
        """اضافه کردن curve contract"""
        try:
            if not self._w3:
                return
            
            curve_address = Web3.to_checksum_address(curve_address)
            
            if curve_address in self._curve_contracts:
                return
            
            contract = self._w3.eth.contract(
                address=curve_address,
                abi=INDIVIDUAL_BONDING_CURVE_ABI
            )
            
            self._curve_contracts[curve_address] = contract
            
            logger.info(f"➕ Added curve contract: {curve_address[:8]}...")
            
        except Exception as e:
            logger.error(f"Failed to add curve contract {curve_address}: {e}")
    
    async def disconnect(self) -> None:
        """Disconnect from blockchain"""
        try:
            # Remove event filters
            for event_filter in self._event_filters:
                try:
                    await self._w3.eth.uninstall_filter(event_filter.filter_id)
                except:
                    pass
            
            self._event_filters.clear()
            
            # Close WebSocket connection
            if self._w3 and self._w3.provider:
                await self._w3.provider.disconnect()
            
            # Close WebSocket connection
            if self._ws_provider:
                await self._ws_provider.disconnect()
            
            self._is_connected = False
            self._w3 = None
            self._ws_provider = None
            
            logger.info("🔌 Blockchain disconnected")
            
        except Exception as e:
            logger.error(f"Error disconnecting blockchain: {e}")
    
    async def is_connected(self) -> bool:
        """وضعیت اتصال"""
        if not self._is_connected or not self._w3:
            return False
        
        try:
            # Test with a simple call
            await self._w3.eth.get_block('latest')
            return True
        except:
            self._is_connected = False
            return False
    
    async def get_latest_block(self) -> int:
        """Get latest block number"""
        if not self._w3:
            raise Exception("Not connected to blockchain")
        
        try:
            block = await self._w3.eth.get_block('latest')
            self._last_block_number = block['number']
            return block['number']
        except Exception as e:
            logger.error(f"Failed to get latest block: {e}")
            raise
    
    async def get_contract_info(self, address: TokenAddress) -> Dict[str, Any]:
        """دریافت اطلاعات contract"""
        if not self._w3:
            raise Exception("Not connected to blockchain")
        
        try:
            checksum_address = Web3.to_checksum_address(address.value)
            
            # Basic info
            code = await asyncio.to_thread(self._w3.eth.get_code, checksum_address)
            balance = await asyncio.to_thread(self._w3.eth.get_balance, checksum_address)
            
            info = {
                'address': checksum_address,
                'has_code': len(code) > 0,
                'balance': str(balance),
                'is_contract': len(code) > 0
            }
            
            # If it's a bonding curve, get more info
            if checksum_address in self._curve_contracts:
                curve_contract = self._curve_contracts[checksum_address]
                try:
                    token_address = await asyncio.to_thread(curve_contract.functions.token().call)
                    creator = await asyncio.to_thread(curve_contract.functions.creator().call)
                    name = await asyncio.to_thread(curve_contract.functions.tokenName().call)
                    symbol = await asyncio.to_thread(curve_contract.functions.tokenSymbol().call)
                    
                    info.update({
                        'type': 'bonding_curve',
                        'token_address': token_address,
                        'creator': creator,
                        'name': name,
                        'symbol': symbol
                    })
                except Exception as e:
                    logger.error(f"Failed to get curve info: {e}")
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get contract info for {address}: {e}")
            raise
    
    async def subscribe_to_events(self) -> AsyncIterator[Dict[str, Any]]:
        """Subscribe به blockchain events"""
        if not self._is_connected or not self._w3:
            raise Exception("Not connected to blockchain")
        
        logger.info("📡 Starting blockchain event subscription...")
        
        try:
            # Setup event filters
            await self._setup_event_filters()
            
            # Start event loop
            while self._is_connected:
                try:
                    events = []
                    
                    # Check all filters for new events
                    for event_filter in self._event_filters:
                        try:
                            new_entries = await event_filter.get_new_entries()
                            for entry in new_entries:
                                event_data = await self._process_log_entry(entry)
                                if event_data:
                                    events.append(event_data)
                                    self._events_received += 1
                        except Exception as e:
                            logger.error(f"Error checking event filter: {e}")
                            continue
                    
                    # Yield events
                    for event in events:
                        yield event
                    
                    # Sleep before next check
                    await asyncio.sleep(0.5)  # Check every 500ms
                    
                except Exception as e:
                    logger.error(f"Error in event subscription loop: {e}")
                    await asyncio.sleep(1)
                    continue
                    
        except Exception as e:
            logger.error(f"Event subscription failed: {e}")
            raise
    
    async def _setup_event_filters(self) -> None:
        """Setup event filters"""
        if not self._w3:
            return
        
        try:
            # Factory events filter
            if self._factory_contract:
                factory_filter = await self._factory_contract.events.BondingCurveDeployed.create_filter(
                    from_block='latest'
                )
                self._event_filters.append(factory_filter)
                logger.info("📡 Factory event filter setup")
            
            # Bonding curve events filters
            for curve_address, curve_contract in self._curve_contracts.items():
                try:
                    # Trade events
                    trade_filter = await curve_contract.events.Trade.create_filter(
                        from_block='latest'
                    )
                    self._event_filters.append(trade_filter)
                    
                    # TokensPurchased events
                    purchase_filter = await curve_contract.events.TokensPurchased.create_filter(
                        from_block='latest'
                    )
                    self._event_filters.append(purchase_filter)
                    
                    # TokensSold events
                    sale_filter = await curve_contract.events.TokensSold.create_filter(
                        from_block='latest'
                    )
                    self._event_filters.append(sale_filter)
                    
                except Exception as e:
                    logger.error(f"Failed to setup filters for {curve_address}: {e}")
                    continue
            
            logger.info(f"📡 Setup {len(self._event_filters)} event filters")
            
        except Exception as e:
            logger.error(f"Failed to setup event filters: {e}")
            raise
    
    async def _process_log_entry(self, log_entry: LogReceipt) -> Optional[Dict[str, Any]]:
        """پردازش log entry"""
        try:
            # Get block info
            block = await self._w3.eth.get_block(log_entry['blockNumber'])
            
            # Get transaction
            tx = await self._w3.eth.get_transaction(log_entry['transactionHash'])
            
            # Determine event type and process
            event_data = None
            
            # Check if it's from factory
            if (self._factory_contract and 
                log_entry['address'].lower() == self._factory_contract.address.lower()):
                event_data = await self._process_factory_event(log_entry, block, tx)
            
            # Check if it's from a bonding curve
            elif log_entry['address'] in self._curve_contracts:
                event_data = await self._process_curve_event(log_entry, block, tx)
            
            return event_data
            
        except Exception as e:
            logger.error(f"Error processing log entry: {e}")
            return None
    
    async def _process_factory_event(
        self, 
        log_entry: LogReceipt, 
        block: Dict[str, Any], 
        tx: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """پردازش factory event"""
        try:
            # Debug log the structure
            logger.debug(f"Factory log_entry structure: {type(log_entry)}, keys: {list(log_entry.keys()) if hasattr(log_entry, 'keys') else 'no keys'}")
            
            # Check if this is already a decoded event from event filter
            if hasattr(log_entry, 'event') and log_entry.event == 'BondingCurveDeployed':
                # Already decoded by event filter
                event_args = log_entry['args']
                logger.info(f"✅ Processing decoded BondingCurveDeployed event: {event_args.get('name', 'unknown')}")
            else:
                # Try to decode manually
                try:
                    decoded_event = self._factory_contract.events.BondingCurveDeployed().process_log(log_entry)
                    event_args = decoded_event['args']
                    logger.info(f"✅ Processing manually decoded BondingCurveDeployed event")
                except Exception as decode_error:
                    logger.error(f"Failed to decode factory event: {decode_error}")
                    logger.debug(f"Log entry details: {log_entry}")
                    return None
            
            # Add new curve contract
            await self._add_curve_contract(event_args['curveAddress'])
            
            return {
                'event_type': 'BondingCurveDeployed',
                'token_address': event_args['tokenAddress'],
                'curve_address': event_args['curveAddress'],
                'creator': event_args['creator'],
                'name': event_args['name'],
                'symbol': event_args['symbol'],
                'timestamp': event_args['timestamp'],
                'block_number': log_entry['blockNumber'],
                'block_timestamp': block['timestamp'],
                'block_hash': block['hash'].hex() if hasattr(block['hash'], 'hex') else str(block['hash']),
                'tx_hash': log_entry['transactionHash'].hex() if hasattr(log_entry['transactionHash'], 'hex') else str(log_entry['transactionHash']),
                'log_index': log_entry['logIndex']
            }
            
        except Exception as e:
            logger.error(f"Error processing factory event: {e}")
            logger.debug(f"Full error details - log_entry: {log_entry}")
            return None
    
    async def _process_curve_event(
        self,
        log_entry: LogReceipt,
        block: Dict[str, Any],
        tx: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """پردازش bonding curve event"""
        try:
            curve_address = log_entry['address']
            curve_contract = self._curve_contracts[curve_address]
            
            # Get token address
            token_address = await curve_contract.functions.token().call()
            
            # Try to decode different event types
            event_data = None
            
            # Check if it's already decoded (from event filter)
            if hasattr(log_entry, 'event') and log_entry.event == 'Trade':
                event_args = log_entry['args']
                
                event_data = {
                    'event_type': 'Trade',
                    'token_address': token_address,
                    'curve_address': curve_address,
                    'user_address': event_args['user'],
                    'is_buy': event_args['isBuy'],
                    'eth_amount': str(event_args['ethInOrOut']),
                    'token_amount': str(event_args['tokenDelta']),
                    'price_before': str(event_args['priceBefore']),
                    'price_after': str(event_args['priceAfter']),
                    'total_supply': str(event_args['supplyAfter']),
                    'timestamp': int(event_args['timestamp']),
                    'block_number': log_entry['blockNumber'],
                    'block_timestamp': block['timestamp'],
                    'block_hash': f"0x{log_entry['blockHash'].hex()}" if hasattr(log_entry['blockHash'], 'hex') else str(log_entry['blockHash']),
                    'tx_hash': f"0x{log_entry['transactionHash'].hex()}" if hasattr(log_entry['transactionHash'], 'hex') else str(log_entry['transactionHash']),
                    'log_index': log_entry['logIndex']
                }
                logger.info(f"🎪 Trade event processed: {event_args['user']} - {event_args['ethInOrOut']} ETH")
                return event_data
                
            elif hasattr(log_entry, 'event') and log_entry.event == 'TokensPurchased':
                event_args = log_entry['args']
                
                event_data = {
                    'event_type': 'TokensPurchased',
                    'token_address': token_address,
                    'curve_address': curve_address,
                    'buyer': event_args['buyer'],
                    'tokens_received': str(event_args['tokensReceived']),
                    'eth_spent': str(event_args['ethSpent']),
                    'platform_fee': str(event_args['platformFee']),
                    'creator_fee': str(event_args['creatorFee']),
                    'new_price': str(event_args['newPrice']),
                    'block_number': log_entry['blockNumber'],
                    'block_timestamp': block['timestamp'],
                    'block_hash': f"0x{log_entry['blockHash'].hex()}" if hasattr(log_entry['blockHash'], 'hex') else str(log_entry['blockHash']),
                    'tx_hash': f"0x{log_entry['transactionHash'].hex()}" if hasattr(log_entry['transactionHash'], 'hex') else str(log_entry['transactionHash']),
                    'log_index': log_entry['logIndex']
                }
                logger.info(f"🎪 TokensPurchased event processed: {event_args['buyer']} - {event_args['tokensReceived']} tokens")
                return event_data
                
            elif hasattr(log_entry, 'event') and log_entry.event == 'TokensSold':
                event_args = log_entry['args']
                
                event_data = {
                    'event_type': 'TokensSold',
                    'token_address': token_address,
                    'curve_address': curve_address,
                    'seller': event_args['seller'],
                    'token_amount': str(event_args['tokenAmount']),
                    'eth_received': str(event_args['ethReceived']),
                    'platform_fee': str(event_args['platformFee']),
                    'creator_fee': str(event_args['creatorFee']),
                    'new_price': str(event_args['newPrice']),
                    'block_number': log_entry['blockNumber'],
                    'block_timestamp': block['timestamp'],
                    'block_hash': f"0x{log_entry['blockHash'].hex()}" if hasattr(log_entry['blockHash'], 'hex') else str(log_entry['blockHash']),
                    'tx_hash': f"0x{log_entry['transactionHash'].hex()}" if hasattr(log_entry['transactionHash'], 'hex') else str(log_entry['transactionHash']),
                    'log_index': log_entry['logIndex']
                }
                logger.info(f"🎪 TokensSold event processed: {event_args['seller']} - {event_args['tokenAmount']} tokens")
                return event_data
                
            else:
                event_name = getattr(log_entry, 'event', 'unknown')
                logger.warning(f"🤷 Unknown curve event '{event_name}' from {curve_address}")
                logger.debug(f"Curve log_entry structure: {type(log_entry)}, data: {log_entry}")
                return None
            
        except Exception as e:
            logger.error(f"Error processing curve event: {e}")
            return None
    
    # Health check and stats
    async def get_connection_stats(self) -> Dict[str, Any]:
        """آمار اتصال"""
        return {
            'is_connected': self._is_connected,
            'chain_id': self.settings.chain_id,
            'factory_address': self.settings.factory_address,
            'ws_url': self.settings.ws_url,
            'last_block_number': self._last_block_number,
            'events_received': self._events_received,
            'curve_contracts': len(self._curve_contracts),
            'event_filters': len(self._event_filters),
            'reconnect_attempts': self._reconnect_attempts
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """بررسی سلامت"""
        try:
            if await self.is_connected():
                latest_block = await self.get_latest_block()
                
                return {
                    'status': 'healthy',
                    'connected': True,
                    'latest_block': latest_block,
                    'chain_id': self.settings.chain_id,
                    'events_received': self._events_received,
                    'curve_contracts': len(self._curve_contracts)
                }
            else:
                return {
                    'status': 'disconnected',
                    'connected': False,
                    'reconnect_attempts': self._reconnect_attempts
                }
                
        except Exception as e:
            logger.error(f"Blockchain health check failed: {e}")
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
